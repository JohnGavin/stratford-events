import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from utils.common import parse_event_date

def fetch_st_brides_events():
    url = "https://www.stbrides.com/whats-on/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching St Brides events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # Found 35 items with 'event' class in check
    # Likely .event-card or similar
    items = soup.find_all(class_=re.compile(r'event', re.I))
    
    for item in items:
        # Avoid navigation/menu items
        if item.name == 'nav' or 'menu' in (item.get('class') or []):
            continue
            
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
        date_str = "See website"
        date_obj = None
        # Try finding date text
        text = item.get_text()
        # Regex for date? Or look for <time>
        date_tag = item.find('time')
        if date_tag:
            date_raw = date_tag.get_text(strip=True)
            date_obj = parse_event_date(date_raw)
            date_str = date_raw

        events.append({
            'title': title,
            'url': event_url,
            'description': "St Brides Event",
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Lunchtime Concerts / Free Events',
            'sub_category': 'St Brides',
            'price': "Free", # Assumption based on user prompt 'public free events'
            'source': 'St Brides'
        })
        
    return events
