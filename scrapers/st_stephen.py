import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from utils.common import parse_event_date

def fetch_st_stephen_events():
    """
    Fetches free musical events from St Stephen Walbrook.
    Uses 'A Church Near You' for structured event data.
    Excludes Evensong, readings, and services.
    """
    url = "https://www.achurchnearyou.com/church/15376/service-and-events/events-all/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching St Stephen Walbrook events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []

    exclude_patterns = re.compile(
        r'evensong|reading|eucharist|communion|prayer|mass|vespers|compline|matins|start:stop|bible|lent',
        re.IGNORECASE
    )
    music_patterns = re.compile(
        r'concert|recital|music|organ|choir|choral|jazz|ensemble|quartet|trio|chamber',
        re.IGNORECASE
    )

    # Parse event blocks from the page
    # "A Church Near You" uses structured event listings
    event_blocks = soup.find_all('div', class_=re.compile(r'event', re.I))
    if not event_blocks:
        # Fallback: look for article or section elements
        event_blocks = soup.find_all(['article', 'section'])

    for block in event_blocks:
        # Title
        title_tag = block.find(re.compile(r'h[2-4]'))
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Skip excluded types (services, readings)
        if exclude_patterns.search(title):
            continue

        # Only include music-related events
        block_text = block.get_text()
        if not music_patterns.search(title) and not music_patterns.search(block_text):
            continue

        # Link
        link_tag = block.find('a', href=True)
        event_url = "https://www.achurchnearyou.com/church/15376/"
        if link_tag:
            href = link_tag.get('href', '')
            if href.startswith('http'):
                event_url = href
            elif href.startswith('/'):
                event_url = f"https://www.achurchnearyou.com{href}"

        # Date
        date_str = "See website"
        date_obj = None
        time_tag = block.find('time')
        if time_tag:
            dt_attr = time_tag.get('datetime', '')
            if dt_attr:
                date_obj = parse_event_date(dt_attr)
            date_str = time_tag.get_text(strip=True) or dt_attr

        if not date_obj:
            # Try text-based date extraction
            text = block.get_text()
            date_match = re.search(
                r'(\d{1,2}\s+\w+\s+\d{4}|\w+day\s+\d{1,2}\s+\w+)',
                text
            )
            if date_match:
                date_obj = parse_event_date(date_match.group())
                if not date_str or date_str == "See website":
                    date_str = date_match.group()

        # Description
        desc_parts = []
        for p in block.find_all('p'):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > 10:
                desc_parts.append(p_text)
        description = " ".join(desc_parts)[:300] if desc_parts else "Free musical event at St Stephen Walbrook"

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'location': 'St Stephen Walbrook, EC4N 8BN',
            'category': 'Lunchtime Concerts / Free Events',
            'sub_category': 'St Stephen Walbrook',
            'price': 'Free',
            'source': 'St Stephen Walbrook'
        })

    # If no structured events found, generate recurring events for the next 4 weeks
    if not events:
        events = _generate_recurring_events()

    return events


def _generate_recurring_events():
    """
    Generate upcoming instances of known recurring free music events
    at St Stephen Walbrook.
    """
    events = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    base_url = "https://www.facebook.com/ststephenec4n/"

    recurring = [
        {
            'title': 'Chamber Music Recital',
            'weekday': 1,  # Tuesday
            'hour': 13, 'minute': 0,
            'description': 'Free chamber music platform concert by visiting performers. Recitals are free with a retiring collection.',
        },
        {
            'title': 'Organ Recital',
            'weekday': 4,  # Friday
            'hour': 12, 'minute': 30,
            'description': 'Free organ recital by visiting organists with a varied programme of works.',
        },
    ]

    # Generate next 4 instances of each recurring event
    for rec in recurring:
        for week_offset in range(4):
            # Find next occurrence
            days_ahead = rec['weekday'] - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            event_date = today + timedelta(days=days_ahead + 7 * week_offset)
            event_date = event_date.replace(hour=rec['hour'], minute=rec['minute'])

            # Skip if in the past
            if event_date < datetime.now():
                continue

            time_str = event_date.strftime("%I:%M%p").lstrip('0').lower()
            date_str = event_date.strftime(f"%A %d %B %Y, {time_str}")

            events.append({
                'title': rec['title'],
                'url': base_url,
                'description': rec['description'],
                'date_str': date_str,
                'date_obj': event_date,
                'location': 'St Stephen Walbrook, EC4N 8BN',
                'category': 'Lunchtime Concerts / Free Events',
                'sub_category': 'St Stephen Walbrook',
                'price': 'Free',
                'source': 'St Stephen Walbrook'
            })

    return events
