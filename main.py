"""Main module for syncing calendar events into Notion."""

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

import pytz
import requests
from dotenv import load_dotenv
from ics import Calendar, Event
from notion_client import Client
from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Iterable

load_dotenv()


CONSOLE = Console()


NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

QUIZ_URL = os.environ.get("QUIZ_URL", "")
LEARN_URL = os.environ.get("LEARN_URL", "")

NZST = pytz.timezone("Pacific/Auckland")

BLACKLIST: set[str] = {"example", "practice"}

HTTP_OK = 200


def get_existing_events() -> list[str]:
    """Return a list of event titles already present in the Notion database."""
    notion = Client(auth=NOTION_TOKEN)
    existing = cast("dict[str, Any]", notion.databases.query(database_id=NOTION_DATABASE_ID))
    results = existing.get("results", [])
    existing_events: list[str] = []

    for result in results:
        try:
            event_name = result["properties"]["Title"]["title"][0]["text"]["content"]
        except IndexError, KeyError:
            continue
        existing_events.append(event_name)

    return existing_events


def fetch_and_merge_calendars() -> Calendar:
    """Fetch remote calendars and merge events into a single Calendar.

    If a remote feed returns a non-ICS body (e.g. an authentication error),
    skip that feed and continue gracefully.
    """
    urls = [("quiz", QUIZ_URL), ("learn", LEARN_URL)]
    merged_cal = Calendar()

    for name, url in urls:
        if not url:
            CONSOLE.print(f"[yellow]Warning:[/yellow] {name} URL not set, skipping")
            continue

        try:
            resp = requests.get(url, timeout=10)
        except requests.RequestException as exc:
            CONSOLE.print(f"[red]Error:[/red] failed to fetch {name} calendar: {exc}")
            continue

        if resp.status_code != HTTP_OK:
            CONSOLE.print(
                f"[yellow]Warning:[/yellow] {name} feed returned HTTP {resp.status_code}, skipping",
            )
            continue

        body = resp.text.strip()
        if not body or body.lower().startswith("invalid") or "error" in body.lower():
            CONSOLE.print(
                f"[yellow]Warning:[/yellow] {name} feed returned non-ICS content, skipping",
            )
            continue

        try:
            cal = Calendar(body)
        except ValueError as exc:
            CONSOLE.print(f"[yellow]Warning:[/yellow] failed to parse {name} feed as ICS: {exc}")
            continue

        for ev in cal.events:
            merged_cal.events.add(ev)

    return merged_cal


def is_blacklisted(name: str) -> bool:
    """Check if the event name contains any blacklisted words."""
    name_lower = name.lower()
    return any(word in name_lower for word in BLACKLIST)


def process_opens_events(
    merged_cal: Calendar,
) -> dict[str, tuple[Any, Any | None, set[str] | None]]:
    """Process events ending with 'opens' and initialize the events dictionary."""
    events: dict[str, tuple[Any, Any | None, set[str] | None]] = {}
    for ev in merged_cal.events:
        if not ev.name or is_blacklisted(ev.name):
            continue
        if ev.name.endswith("opens"):
            base_name = ev.name.replace(" opens", "")
            events[base_name] = (ev.begin, None, ev.categories)
    return events


def process_closing_events(
    merged_cal: Calendar,
    events: dict[str, tuple[Any, Any | None, set[str] | None]],
) -> None:
    """Process events ending with 'closes' or 'should be completed' and update dictionary."""
    for ev in merged_cal.events:
        if not ev.name:
            continue

        if ev.name.endswith("should be completed"):
            base_name = ev.name.replace(" should be completed", "")
            if base_name in events:
                start, _, _ = events[base_name]
                events[base_name] = (start, ev.begin, ev.categories)

        elif ev.name.endswith("closes"):
            base_name = ev.name.replace(" closes", "")
            if base_name in events:
                start, end, _ = events[base_name]
                if end is None:
                    events[base_name] = (start, ev.begin, ev.categories)
            elif not is_blacklisted(base_name):
                events[base_name] = (
                    datetime(1900, 1, 1, tzinfo=pytz.UTC).astimezone(NZST),
                    ev.begin,
                    ev.categories,
                )


def read_calendar() -> Calendar:
    """Read remote calendars, merge them and return synthesized events.

    The function looks for event pairs such as "<name> opens" and
    "<name> closes" (or "<name> should be completed") and builds
    a calendar with those intervals.
    """
    merged_cal = fetch_and_merge_calendars()
    events = process_opens_events(merged_cal)
    process_closing_events(merged_cal, events)

    calendar = Calendar()
    for name, (begin, end, categories) in events.items():
        if end is None:
            continue
        new_ev = Event()
        new_ev.name = name
        new_ev.begin = begin
        new_ev.end = end
        new_ev.categories = categories or set()
        calendar.events.add(new_ev)

    return calendar


def create_notion_pages(calendar: Calendar, existing_events: Iterable[str]) -> None:
    """Create Notion pages for events that don't already exist."""
    notion = Client(auth=NOTION_TOKEN)

    for ev in calendar.events:
        name = ev.name
        if not name or name in existing_events:
            continue

        date = ev.end.astimezone(NZST).isoformat()

        course = ""
        if ev.categories:
            course = next(iter(ev.categories)).split("-")[0]

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Title": {"title": [{"text": {"content": name}}]},
                "Date": {"date": {"start": date}},
                "Tags": {"multi_select": [{"name": course}]},
                "Priority Level": {"select": {"name": "No Priority"}},
            },
        )


def update_statuses(calendar: Calendar) -> None:
    """Update 'Priority Level' for pages whose open time has passed."""
    notion = Client(auth=NOTION_TOKEN)
    current_time = datetime.now(NZST)

    database = cast("dict[str, Any]", notion.databases.query(database_id=NOTION_DATABASE_ID))

    pages: dict[str, tuple[str, dict[str, Any] | None]] = {}
    for result in database.get("results", []):
        try:
            page_name = result["properties"]["Title"]["title"][0]["text"]["content"]
            page_status = result["properties"]["Priority Level"]["select"]
            page_id = result["id"]
        except KeyError, IndexError:
            continue
        pages[page_name] = (page_id, page_status)

    for ev in calendar.events:
        if not ev.name:
            continue
        page = pages.get(ev.name)
        if page is None:
            continue
        page_id, page_status = page

        if page_status is not None:
            continue

        open_time = ev.begin.astimezone(NZST)
        close_time = ev.end.astimezone(NZST)

        if current_time > open_time or open_time == close_time:
            notion.pages.update(
                page_id=page_id,
                properties={"Priority Level": {"select": {"name": "Low Priority"}}},
            )


def main() -> None:
    """Entry point for the script."""
    with CONSOLE.status("Reading calendar..."):
        calendar = read_calendar()
    CONSOLE.print("[green]✓[/green] Calendar loaded")

    with CONSOLE.status("Getting existing events..."):
        existing_events = get_existing_events()
    CONSOLE.print("[green]✓[/green] Existing events fetched")

    with CONSOLE.status("Creating new Notion pages..."):
        create_notion_pages(calendar, existing_events)
    CONSOLE.print("[green]✓[/green] Notion pages created")

    with CONSOLE.status("Updating statuses..."):
        update_statuses(calendar)
    CONSOLE.print("[green]✓[/green] Statuses updated")
    CONSOLE.print("[bold green]Done![/bold green]")


if __name__ == "__main__":
    main()
