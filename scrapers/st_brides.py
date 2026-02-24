import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from utils.common import parse_event_date

def fetch_st_brides_events():
    """
    Fetches free lunchtime recitals from St Bride's Church.
    Returns specific event details (artist, programme, date/time).
    Excludes services (Morning Prayer, Evensong, Communion, etc).
    """
    url = "https://www.stbrides.com/whats-on/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching St Brides events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []

    # Patterns to exclude (services, not concerts)
    exclude_patterns = re.compile(
        r'morning prayer|evensong|communion|eucharist|space for silence|compline|vespers|matins|bible|lent course',
        re.IGNORECASE
    )
    # Patterns to include (musical events)
    music_patterns = re.compile(
        r'recital|concert|piano|organ|choir|violin|cello|guitar|soprano|mezzo|tenor|baritone|bass|singers|ensemble|quartet|trio|harp|flute|oboe|clarinet|trumpet|stabat|cantorum|scholars',
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
        if not title or len(title) < 3:
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
                event_url = f"https://www.stbrides.com{href}"

        # Date and time
        date_str = "See website"
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
                        t = datetime.strptime(time_str.strip(), "%I:%M%p")
                    else:
                        t = datetime.strptime(time_str.strip(), "%H:%M")
                    date_obj = date_obj.replace(hour=t.hour, minute=t.minute)
                except ValueError:
                    pass

        # Build description from text content
        desc_parts = []
        for p in item.find_all(['p', 'span', 'div']):
            p_text = p.get_text(strip=True)
            if p_text and len(p_text) > 5 and not exclude_patterns.search(p_text):
                # Skip if it's just the title repeated
                if p_text.lower() != title.lower():
                    desc_parts.append(p_text)
        description = " | ".join(dict.fromkeys(desc_parts))[:300] if desc_parts else title
        if not description or description == title:
            description = f"Free lunchtime recital at St Bride's Church, Fleet Street"

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'location': "St Bride's Church, Fleet Street",
            'category': 'Lunchtime Concerts / Free Events',
            'sub_category': "St Bride's",
            'price': "Free",
            'source': "St Bride's"
        })

    return events
