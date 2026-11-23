import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date
from params import (
    BARTS_DESCRIPTION,
    BARTS_EVENTS_URL,
    CATEGORY_STEM,
    DATE_SEE_WEBSITE,
    HTML_PARSER,
    PRICE_CHECK_WEBSITE,
    SOURCE_BARTS,
    SUB_MUSEUM,
    USER_AGENT_BROWSER,
)

def fetch_barts_north_wing_events():
    url = BARTS_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Barts events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []
    
    # Structure based on "What's On" usually articles
    items = soup.find_all('article')
    
    for item in items:
        # Title
        title_tag = item.find(re.compile(r'h[2-4]'))
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # Link
        link_tag = item.find('a')
        event_url = url
        if link_tag and link_tag.get('href'):
            event_url = link_tag.get('href')
            
        # Date
        date_tag = item.find('time')
        date_str = DATE_SEE_WEBSITE
        date_obj = None
        if date_tag:
            date_raw = date_tag.get_text(strip=True)
            date_obj = parse_event_date(date_raw)
            date_str = date_raw
        else:
            # Try finding date in text
            pass

        # Filter "Public events only"
        # If there are categories, maybe check them.
        # Assuming all listed here are public.

        events.append({
            'title': title,
            'url': event_url,
            'description': BARTS_DESCRIPTION,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': CATEGORY_STEM, # Or Culture
            'sub_category': SUB_MUSEUM,
            'price': PRICE_CHECK_WEBSITE,
            'source': SOURCE_BARTS
        })
        
    return events
