import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date

def fetch_aquatics_events():
    url = "https://www.londonaquaticscentre.org/events/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Aquatics events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # Target The Events Calendar structure
    rows = soup.find_all(class_='tribe-events-calendar-list__event-row')
    
    for row in rows:
        # Title
        title_tag = row.find('h3') 
        if not title_tag: 
            title_tag = row.find('h4') # Fallback
            
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # Link
        link_tag = title_tag.find('a')
        event_url = url
        if link_tag and link_tag.get('href'):
            event_url = link_tag.get('href')
            
        # Date
        # Look for <time> tag
        date_str = "See website"
        date_obj = None
        
        time_tag = row.find('time')
        if time_tag and time_tag.get('datetime'):
            # datetime attr usually YYYY-MM-DD
            raw_date = time_tag.get('datetime')
            try:
                date_obj = datetime.strptime(raw_date, "%Y-%m-%d")
                date_str = date_obj.strftime("%a, %d %b %Y")
            except:
                pass
        
        # Description
        description = ""
        desc_div = row.find(class_='tribe-events-calendar-list__event-description')
        if desc_div:
            description = desc_div.get_text(strip=True)[:300] + "..."

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Sports',
            'sub_category': 'Swimming / Aquatics',
            'price': "Check website",
            'source': 'London Aquatics Centre'
        })
        
    return events