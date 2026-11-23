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
    LSO_BASE_URL,
    LSO_CATEGORY_MAX_CHARS,
    LSO_DESCRIPTION,
    LSO_EVENTS_URL,
    LSO_LOCATION,
    PRICE_FREE,
    SOURCE_LSO,
    TIME_12H_FORMAT,
    USER_AGENT_BROWSER,
)

def fetch_lso_events():
    """
    Fetches LSO Free Friday Lunchtime Concerts with specific details
    (title, date, time, description, direct link).
    """
    url = LSO_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }

    try:
        response = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching LSO events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []

    # Find all event links - LSO uses <a> blocks containing h3, p elements
    # Try multiple selectors for robustness
    items = soup.find_all(class_=re.compile(r'c-card'))
    if not items:
        # Fallback: find all links that point to /whats-on/ event pages
        items = soup.find_all('a', href=re.compile(r'/whats-on/.*concert.*|/whats-on/.*lunchtime.*|/whats-on/.*relaxed.*'))
        if not items:
            # Broader fallback: any <a> with an h3 inside
            items = [a for a in soup.find_all('a', href=True) if a.find('h3')]

    seen_urls = set()

    for item in items:
        # Get the link element
        if item.name == 'a':
            link_tag = item
        else:
            link_tag = item.find('a', href=True)

        event_url = url
        if link_tag and link_tag.get('href'):
            href = link_tag['href']
            if href.startswith('/'):
                event_url = f"{LSO_BASE_URL}{href}"
            elif href.startswith('http'):
                event_url = href

        # Deduplicate by URL
        if event_url in seen_urls:
            continue
        seen_urls.add(event_url)

        # Title from h3
        title_tag = item.find('h3')
        if not title_tag:
            title_tag = item.find(class_=re.compile(r'title'))
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Extract all paragraph text to find date/time and description
        paragraphs = item.find_all('p')
        date_str = DATE_SEE_WEBSITE
        date_obj = None
        description_parts = []
        category_text = ""

        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if not p_text:
                continue

            # Check if this looks like a date line (contains month name and time)
            if re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}', p_text):
                date_str = p_text
                # Parse the date - format like "Friday 27 February 2026 • 12.30pm"
                # Clean up bullet/dot separator
                clean = p_text.replace('•', ' ').replace('·', ' ')
                # Try to extract date and time
                date_match = re.search(
                    r'(\w+day\s+\d{1,2}\s+\w+\s+\d{4})',
                    clean
                )
                time_match = re.search(r'(\d{1,2}[.:]\d{2}\s*[ap]m)', clean, re.I)

                if date_match:
                    date_part = date_match.group(1)
                    date_obj = parse_event_date(date_part)

                    if date_obj and time_match:
                        time_part = time_match.group(1).replace('.', ':')
                        try:
                            t = datetime.strptime(time_part.strip(), TIME_12H_FORMAT)
                            date_obj = date_obj.replace(hour=t.hour, minute=t.minute)
                        except ValueError:
                            pass

            elif len(p_text) < LSO_CATEGORY_MAX_CHARS and not description_parts:
                # Short text before date is likely category (e.g., "LSO Discovery")
                category_text = p_text
            else:
                # Description text
                description_parts.append(p_text)

        # Build rich description
        desc = ""
        if category_text:
            desc = f"{category_text}. "
        if description_parts:
            desc += " ".join(description_parts)
        if not desc:
            desc = LSO_DESCRIPTION
        if len(desc) > DESCRIPTION_MAX_CHARS:
            desc = desc[:DESCRIPTION_MAX_CHARS] + "..."

        events.append({
            'title': title,
            'url': event_url,
            'description': desc,
            'date_str': date_str,
            'date_obj': date_obj,
            'location': LSO_LOCATION,
            'category': CATEGORY_FREE_CONCERTS,
            'sub_category': LSO_LOCATION,
            'price': PRICE_FREE,
            'source': SOURCE_LSO
        })

    return events
