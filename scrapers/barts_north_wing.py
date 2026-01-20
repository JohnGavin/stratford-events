import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date

def fetch_barts_north_wing_events():
    url = "https://bartsnorthwing.org.uk/whats-on/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Barts events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
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
        date_str = "See website"
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
            'description': "Barts North Wing Event",
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'STEM / Factual', # Or Culture
            'sub_category': 'Museum / Exhibition',
            'price': "Check website",
            'source': 'Barts North Wing'
        })
        
    return events
