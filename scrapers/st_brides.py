import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from utils.common import parse_event_date
from params import (
    CATEGORY_FREE_CONCERTS,
    DATE_SEE_WEBSITE,
    DESCRIPTION_MAX_CHARS,
    HTML_PARSER,
    HTTP_TIMEOUT_SECONDS,
    PRICE_FREE,
    SOURCE_ST_BRIDES,
    ST_BRIDES_BASE_URL,
    ST_BRIDES_DESCRIPTION,
    ST_BRIDES_EVENTS_URL,
    ST_BRIDES_EXCLUDE_PATTERN,
    ST_BRIDES_LOCATION,
    ST_BRIDES_MIN_TEXT_CHARS,
    ST_BRIDES_MIN_TITLE_CHARS,
    ST_BRIDES_MUSIC_PATTERN,
    ST_BRIDES_USER_AGENT,
    TIME_12H_FORMAT,
    TIME_24H_FORMAT,
)

def fetch_st_brides_events():
    """
    Fetches free lunchtime recitals from St Bride's Church.
    Returns specific event details (artist, programme, date/time).
    Excludes services (Morning Prayer, Evensong, Communion, etc).
    """
    url = ST_BRIDES_EVENTS_URL
    headers = {
        "User-Agent": ST_BRIDES_USER_AGENT
    }

    try:
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching St Brides events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []

    # Patterns to exclude (services, not concerts)
    exclude_patterns = re.compile(
        ST_BRIDES_EXCLUDE_PATTERN,
        re.IGNORECASE
    )
    # Patterns to include (musical events)
    music_patterns = re.compile(
        ST_BRIDES_MUSIC_PATTERN,
        re.IGNORECASE
    )

    # St Brides uses accordion sections and event listings
    # Try multiple selectors
    items = soup.find_all(class_=re.compile(r'event|acc|concert|recital', re.I))
    if not items:
        # Broader: look for headings with dates
        items = soup.find_all(['div', 'article', 'section'])

    seen_titles = set()

    for item in items:
        # Skip navigation/menu items
        if item.name in ['nav', 'header', 'footer']:
            continue
        tag_classes = ' '.join(item.get('class', []))
        if 'menu' in tag_classes or 'nav' in tag_classes:
            continue

        # Title - look for heading tags
        title_tag = item.find(re.compile(r'h[2-5]'))
        if not title_tag:
            # Try button text (accordion pattern)
            title_tag = item.find('button')
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        if not title or len(title) < ST_BRIDES_MIN_TITLE_CHARS:
            continue

        # Skip excluded types
        if exclude_patterns.search(title):
            continue

        # Only include music-related events
        item_text = item.get_text()
        if not music_patterns.search(title) and not music_patterns.search(item_text):
            continue

        # Deduplicate
        title_key = title.lower().strip()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        # Link
        link_tag = item.find('a', href=True)
        event_url = url
        if link_tag:
            href = link_tag.get('href', '')
            if href.startswith('http'):
                event_url = href
            elif href.startswith('/'):
                event_url = f"{ST_BRIDES_BASE_URL}{href}"

        # Date and time
        date_str = DATE_SEE_WEBSITE
        date_obj = None

        # Look for <time> tag first
        time_tag = item.find('time')
        if time_tag:
            dt_attr = time_tag.get('datetime', '')
            if dt_attr:
                date_obj = parse_event_date(dt_attr)
            date_str = time_tag.get_text(strip=True) or dt_attr

        # Try date class
        if not date_obj:
            date_tag = item.find(class_=re.compile(r'date', re.I))
            if date_tag:
                date_raw = date_tag.get_text(strip=True)
                date_obj = parse_event_date(date_raw)
                date_str = date_raw

        # Try extracting date from text
        if not date_obj:
            date_match = re.search(
                r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[,]?\s+'
                r'(\d{1,2})\s+'
                r'(January|February|March|April|May|June|July|August|September|October|November|December)',
                item_text
            )
            if date_match:
                year = datetime.now().year
                date_text = f"{date_match.group(1)} {date_match.group(2)} {year}"
                date_obj = parse_event_date(date_text)
                date_str = date_match.group(0)

        # Extract time if not already in date_obj
        if date_obj:
            time_match = re.search(r'(\d{1,2}[.:]\d{2}\s*[ap]m|\d{1,2}:\d{2})', item_text, re.I)
            if time_match and date_obj.hour == 0:
                time_str = time_match.group(1).replace('.', ':')
                try:
                    if 'am' in time_str.lower() or 'pm' in time_str.lower():
                        t = datetime.strptime(time_str.strip(), TIME_12H_FORMAT)
                    else:
                        t = datetime.strptime(time_str.strip(), TIME_24H_FORMAT)
                    date_obj = date_obj.replace(hour=t.hour, minute=t.minute)
                except ValueError:
                    pass

        # Build description from text content
        desc_parts = []
        for p in item.find_all(['p', 'span', 'div']):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > ST_BRIDES_MIN_TEXT_CHARS and not exclude_patterns.search(p_text):
                # Skip if it's just the title repeated
                if p_text.lower() != title.lower():
                    desc_parts.append(p_text)
        description = " | ".join(dict.fromkeys(desc_parts))[:DESCRIPTION_MAX_CHARS] if desc_parts else title
        if not description or description == title:
            description = ST_BRIDES_DESCRIPTION

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'location': ST_BRIDES_LOCATION,
            'category': CATEGORY_FREE_CONCERTS,
            'sub_category': SOURCE_ST_BRIDES,
            'price': PRICE_FREE,
            'source': SOURCE_ST_BRIDES
        })

    return events
