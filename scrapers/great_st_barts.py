import requests
from datetime import datetime, timedelta
import re
from params import (
    CATEGORY_FREE_CONCERTS,
    DATE_SEE_WEBSITE,
    DESCRIPTION_MAX_CHARS,
    GREAT_ST_BARTS_API_URL_TEMPLATE,
    GREAT_ST_BARTS_DESCRIPTION,
    GREAT_ST_BARTS_EVENT_URL_TEMPLATE,
    GREAT_ST_BARTS_EXCLUDE_PATTERN,
    GREAT_ST_BARTS_FALLBACK_URL,
    GREAT_ST_BARTS_LOCATION,
    GREAT_ST_BARTS_MUSIC_PATTERN,
    GREAT_ST_BARTS_USER_AGENT,
    HTTP_TIMEOUT_SECONDS,
    ISO_DATE_FORMAT,
    LONG_DATETIME_12H_FORMAT,
    PRICE_FREE,
    REPORT_HORIZON_WEEKS,
    SOURCE_GREAT_ST_BARTS,
)

def fetch_great_st_barts_events():
    """
    Fetches free musical events from Great St Barts via ChurchSuite API.
    Excludes Evensong and readings.
    """
    # Fetch events up to the report horizon
    today = datetime.now().strftime(ISO_DATE_FORMAT)
    end = (datetime.now() + timedelta(weeks=REPORT_HORIZON_WEEKS)).strftime(ISO_DATE_FORMAT)
    api_url = GREAT_ST_BARTS_API_URL_TEMPLATE.format(start=today, end=end)

    headers = {
        "User-Agent": GREAT_ST_BARTS_USER_AGENT
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching Great St Barts events: {e}")
        return []

    events = []
    exclude_patterns = re.compile(
        GREAT_ST_BARTS_EXCLUDE_PATTERN,
        re.IGNORECASE
    )
    music_patterns = re.compile(
        GREAT_ST_BARTS_MUSIC_PATTERN,
        re.IGNORECASE
    )

    for item in data:
        name = item.get('name', '')

        # Skip excluded event types
        if exclude_patterns.search(name):
            continue

        # Check category or title for music-related content
        category = item.get('category', {})
        cat_name = category.get('name', '') if isinstance(category, dict) else ''
        combined = f"{name} {cat_name}"

        if not music_patterns.search(combined):
            continue

        # Parse dates
        dt_start = item.get('datetime_start', '')
        date_obj = None
        date_str = DATE_SEE_WEBSITE
        if dt_start:
            try:
                date_obj = datetime.fromisoformat(dt_start.replace('Z', '+00:00'))
                date_str = date_obj.strftime(LONG_DATETIME_12H_FORMAT).replace(' 0', ' ')
            except (ValueError, TypeError):
                pass

        # Build description from event details
        description = item.get('description', '')
        if description:
            # Strip HTML tags
            description = re.sub(r'<[^>]+>', ' ', description).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > DESCRIPTION_MAX_CHARS:
                description = description[:DESCRIPTION_MAX_CHARS] + "..."

        # Check ticket price - only include free events
        signup = item.get('signup_options', {})
        tickets = signup.get('tickets', {}) if isinstance(signup, dict) else {}
        # If tickets have a price > 0, skip
        if isinstance(tickets, dict) and tickets.get('price'):
            try:
                price_val = float(str(tickets['price']).replace('£', ''))
                if price_val > 0:
                    continue
            except (ValueError, TypeError):
                pass

        # Build event URL
        identifier = item.get('identifier', '')
        event_url = GREAT_ST_BARTS_FALLBACK_URL
        if identifier:
            event_url = GREAT_ST_BARTS_EVENT_URL_TEMPLATE.format(identifier=identifier)

        events.append({
            'title': name,
            'url': event_url,
            'description': description or GREAT_ST_BARTS_DESCRIPTION,
            'date_str': date_str,
            'date_obj': date_obj,
            'location': GREAT_ST_BARTS_LOCATION,
            'category': CATEGORY_FREE_CONCERTS,
            'sub_category': SOURCE_GREAT_ST_BARTS,
            'price': PRICE_FREE,
            'source': SOURCE_GREAT_ST_BARTS
        })

    return events
