import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from utils.common import parse_event_date

def fetch_lso_events():
    url = "https://www.lso.co.uk/whats-on/?category=free-friday-lunchtime-concerts"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching LSO events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # LSO listing items
    # Typically <div class="c-card ..."> or <article>
    items = soup.find_all(class_=re.compile(r'c-card\s|c-card$'))
    
    for item in items:
        # Title
        title_tag = item.find(class_=re.compile(r'title'))
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # Link
        link_tag = item.find('a')
        event_url = url
        if link_tag and link_tag.get('href'):
            event_url = link_tag.get('href')
            
        # Date
        # Usually in .c-card__date or similar
        date_tag = item.find(class_=re.compile(r'date'))
        date_str = "See website"
        date_obj = None
        if date_tag:
            date_raw = date_tag.get_text(strip=True)
            date_obj = parse_event_date(date_raw)
            date_str = date_raw

        events.append({
            'title': title,
            'url': event_url,
            'description': "Free Friday Lunchtime Concert",
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Lunchtime Concerts / Free Events',
            'sub_category': 'LSO St Luke\'s',
            'price': "Free",
            'source': 'LSO'
        })
        
    return events
