"""main"""

import os
from datetime import datetime

import pytz
import requests
from ics import Calendar
from notion_client import Client


NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

QUIZ_URL = os.environ["QUIZ_URL"]
LEARN_URL = os.environ["LEARN_URL"]

NZST = pytz.timezone('Pacific/Auckland')


def get_existing_events():
    """get existing events"""
    notion = Client(auth=NOTION_TOKEN)
    existing = notion.databases.query(database_id=NOTION_DATABASE_ID)
    results = existing['results']
    existing_events = []

    for result in results:
        try:
            event_name = result['properties']['Name']['title'][0]['text']['content']
            existing_events.append(event_name)
        except (IndexError, KeyError):
            continue
    return existing_events


def read_calendar():
    """read calendar"""
    quiz_cal = Calendar(requests.get(QUIZ_URL, timeout=10).text)
    learn_cal = Calendar(requests.get(LEARN_URL, timeout=10).text)

    merged_cal = Calendar()
    for event in quiz_cal.events:
        merged_cal.events.add(event)
    for event in learn_cal.events:
        merged_cal.events.add(event)

    opening_times = {}
    for event in merged_cal.events:
        if event.name.endswith("opens"):
            base_name = event.name.replace(" opens", "")
            opening_times[base_name] = event.begin

    calendar = Calendar()
    for event in merged_cal.events:
        if event.name.endswith("closes"):
            stripped_name = event.name.replace(" closes", "")
            if stripped_name in opening_times:
                event.begin = opening_times[stripped_name]
            event.name = stripped_name
            calendar.events.add(event)

    return calendar


def create_notion_pages(calendar: Calendar, existing_events):
    """create notion page"""
    notion = Client(auth=NOTION_TOKEN)

    for event in calendar.events:
        name = event.name

        if name in existing_events:
            continue

        date = event.end.astimezone(NZST).isoformat()

        course = list(event.categories)[0].split("-")[0]

        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                },
                "Due Date": {
                    "date": {
                        "start": date
                    }
                },
                "Course": {
                    "select": {
                        "name": course
                    }
                }
            }
        )


def update_statuses(calendar: Calendar):
    """updates the statuses of each event"""
    notion = Client(auth=NOTION_TOKEN)
    current_time = datetime.now(NZST)

    # Retrieve all pages to get their IDs
    database = notion.databases.query(database_id=NOTION_DATABASE_ID)

    # Create a mapping of event names to page IDs
    pages = {}
    for result in database['results']:
        try:
            page_name = result['properties']['Name']['title'][0]['text']['content']
            page_status = result['properties']['Status']['status']['name']
            page_id = result['id']
            pages[page_name] = (page_id, page_status)
        except (KeyError, IndexError):
            continue

    for event in calendar.events:
        page_id, page_status = pages[event.name]

        if page_status != "Upcoming":
            continue

        open_time = event.begin.astimezone(NZST)
        close_time = event.end.astimezone(NZST)

        if current_time > open_time or open_time == close_time:
            notion.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {
                            "name": "Open"
                        }
                    }
                }
            )



def main():
    """main"""
    message = "Reading calendar... "
    print(message)
    calendar = read_calendar()
    print(f"\033[F\033[{len(message)}G✅")

    message = "Getting existing events... "
    print(message)
    existing_events = get_existing_events()
    print(f"\033[F\033[{len(message)}G✅")

    message = "Creating new Notion pages... "
    print(message)
    create_notion_pages(calendar, existing_events)
    print(f"\033[F\033[{len(message)}G✅")

    message = "Updating statuses... "
    print(message)
    update_statuses(calendar)
    print(f"\033[F\033[{len(message)}G✅")
    print("Done!")


if __name__ == "__main__":
    main()
