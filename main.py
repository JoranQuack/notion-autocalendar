"""main"""

import os

import pytz
import requests
from ics import Calendar
from notion_client import Client

from constants import COURSE_COLOURS, LEARN_URL, QUIZ_URL


def get_existing_events():
    """get existing events"""
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    existing = notion.databases.query(database_id=os.environ["NOTION_DATABASE_ID"])
    results = existing['results']
    existing_events = []
    try:
        for result in results:
            event = result['properties']['Name']['title'][0]['text']['content']
            existing_events.append(event)
        return existing_events
    except KeyError:
        return []


def read_calendar(existing_events):
    """read calendar"""
    calendar = Calendar()
    quiz_cal = Calendar(requests.get(QUIZ_URL, timeout=10).text)
    learn_cal = Calendar(requests.get(LEARN_URL, timeout=10).text)

    for event in quiz_cal.events:
        stripped_name = event.name.replace(" closes", "")
        if event.name.endswith("closes") and stripped_name not in existing_events:
            calendar.events.add(event)

    for event in learn_cal.events:
        stripped_name = event.name.replace(" closes", "")
        if event.name.endswith("closes") and stripped_name not in existing_events:
            calendar.events.add(event)

    return calendar


def create_notion_page(calendar: Calendar):
    """create notion page"""
    notion = Client(auth=os.environ["NOTION_TOKEN"])
    nzst = pytz.timezone('Pacific/Auckland')

    for event in calendar.events:
        name = event.name.replace(" closes", "")

        date_utc = event.begin
        date_nzst = date_utc.astimezone(nzst).isoformat()

        course_name = list(event.categories)[0].split("-")[0]
        course = f"{COURSE_COLOURS[course_name]} {course_name}"

        notion.pages.create(
            parent={"database_id": os.environ["NOTION_DATABASE_ID"]},
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
                        "start": date_nzst
                    }
                },
                "Course": {
                    "rich_text": [
                        {
                            "text": {
                                "content": course
                            }
                        }
                    ]
                }
            }
        )



def main():
    """main"""
    message = "Getting existing events... "
    print(message)
    existing_events = get_existing_events()
    print(f"\033[F\033[{len(message)}G✅")

    message = "Reading calendar... "
    print(message)
    calendar = read_calendar(existing_events)
    print(f"\033[F\033[{len(message)}G✅")

    message = "Creating Notion page... "
    print(message)
    create_notion_page(calendar)
    print(f"\033[F\033[{len(message)}G✅")
    print("Done!")



if __name__ == "__main__":
    main()
