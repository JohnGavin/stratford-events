import requests
from datetime import datetime, timedelta
import re

def fetch_great_st_barts_events():
    """
    Fetches free musical events from Great St Barts via ChurchSuite API.
    Excludes Evensong and readings.
    """
    # Fetch next 8 weeks of events
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(weeks=8)).strftime("%Y-%m-%d")
    api_url = f"https://greatstbarts.churchsuite.com/embed/calendar/json?date_start={today}&date_end={end}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching Great St Barts events: {e}")
        return []

    events = []
    exclude_patterns = re.compile(
        r'evensong|reading|eucharist|communion|prayer|mass|vespers|compline|matins',
        re.IGNORECASE
    )
    music_patterns = re.compile(
        r'concert|recital|music|organ|choir|singing|jazz|ensemble|quartet|trio|sonata|symphony',
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
        date_str = "See website"
        if dt_start:
            try:
                date_obj = datetime.fromisoformat(dt_start.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%A %d %B %Y, %I:%M%p").replace(' 0', ' ')
            except (ValueError, TypeError):
                pass

        # Build description from event details
        description = item.get('description', '')
        if description:
            # Strip HTML tags
            description = re.sub(r'<[^>]+>', ' ', description).strip()
            description = re.sub(r'\s+', ' ', description)
            if len(description) > 300:
                description = description[:300] + "..."

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
        event_url = f"https://www.greatstbarts.com/events"
        if identifier:
            event_url = f"https://greatstbarts.churchsuite.com/events/{identifier}"

        events.append({
            'title': name,
            'url': event_url,
            'description': description or "Free musical event at Great St Barts",
            'date_str': date_str,
            'date_obj': date_obj,
            'location': 'Great St Bartholomew\'s Church',
            'category': 'Lunchtime Concerts / Free Events',
            'sub_category': 'Great St Barts',
            'price': 'Free',
            'source': 'Great St Barts'
        })

    return events
