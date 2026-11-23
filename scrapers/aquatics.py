import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date
from params import (
    AQUATICS_DISRUPTION_KEYWORDS,
    AQUATICS_EVENTS_URL,
    CATEGORY_SPORTS,
    DATE_SEE_WEBSITE,
    DESCRIPTION_MAX_CHARS,
    DISPLAY_DATE_FORMAT,
    HTML_PARSER,
    ISO_DATE_FORMAT,
    MONTHS_PER_YEAR,
    PRICE_CHECK_WEBSITE,
    SOURCE_AQUATICS,
    SUB_AQUATICS,
    USER_AGENT_BROWSER,
)

def fetch_aquatics_events():
    url = AQUATICS_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Aquatics events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []

    # Current month and next month are allowed for disruption notices
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    next_month = current_month + 1 if current_month < MONTHS_PER_YEAR else 1
    next_year = current_year if current_month < MONTHS_PER_YEAR else current_year + 1

    # Target The Events Calendar structure
    rows = soup.find_all(class_='tribe-events-calendar-list__event-row')

    for row in rows:
        # Title
        title_tag = row.find('h3')
        if not title_tag:
            title_tag = row.find('h4')  # Fallback

        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Link
        link_tag = title_tag.find('a')
        event_url = url
        if link_tag and link_tag.get('href'):
            event_url = link_tag.get('href')

        # Date
        date_str = DATE_SEE_WEBSITE
        date_obj = None

        time_tag = row.find('time')
        if time_tag and time_tag.get('datetime'):
            raw_date = time_tag.get('datetime')
            try:
                date_obj = datetime.strptime(raw_date, ISO_DATE_FORMAT)
                date_str = date_obj.strftime(DISPLAY_DATE_FORMAT)
            except (ValueError, TypeError):
                pass

        # Filter disruption/closure notices by date proximity
        title_lower = title.lower()
        is_disruption = any(x in title_lower for x in AQUATICS_DISRUPTION_KEYWORDS)

        if is_disruption:
            if date_obj:
                event_month = date_obj.month
                event_year = date_obj.year
                # Only allow current month and next month
                is_current = (event_month == current_month and event_year == current_year)
                is_next = (event_month == next_month and event_year == next_year)
                if not (is_current or is_next):
                    continue
            else:
                # No date on a disruption notice - skip it
                continue

        # Description
        description = ""
        desc_div = row.find(class_='tribe-events-calendar-list__event-description')
        if desc_div:
            description = desc_div.get_text(strip=True)[:DESCRIPTION_MAX_CHARS] + "..."

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': CATEGORY_SPORTS,
            'sub_category': SUB_AQUATICS,
            'price': PRICE_CHECK_WEBSITE,
            'source': SOURCE_AQUATICS
        })

    return events
