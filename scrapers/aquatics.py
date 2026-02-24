import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date

def fetch_aquatics_events():
    url = "https://www.londonaquaticscentre.org/events/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Aquatics events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []

    # Current month and next month are allowed for disruption notices
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1

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
        date_str = "See website"
        date_obj = None

        time_tag = row.find('time')
        if time_tag and time_tag.get('datetime'):
            raw_date = time_tag.get('datetime')
            try:
                date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
                date_str = date_obj.strftime("%a, %d %b %Y")
            except (ValueError, TypeError):
                pass

        # Filter disruption/closure notices by date proximity
        title_lower = title.lower()
        is_disruption = any(x in title_lower for x in [
            'disruption', 'closure', 'update', 'info', 'notice'
        ])

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
            description = desc_div.get_text(strip=True)[:300] + "..."

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Sports',
            'sub_category': 'Swimming / Aquatics',
            'price': "Check website",
            'source': 'London Aquatics Centre'
        })

    return events
