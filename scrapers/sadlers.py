import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_sadlers_events():
    # Sadler's Wells East specific URL or search
    # Often they list community events separately.
    # Trying the main what's on with query for East
    url = "https://www.sadlerswells.com/whats-on/?location=sadlers-wells-east"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        # Sadler's might handle filters via JS. If so, we might need a broader scrape.
        # Fallback to main list and filter by text "Sadler's Wells East"
    except:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # This selector is a guess based on standard implementations, 
    # might need adjustment if I could see the HTML.
    # Assuming cards with titles.
    cards = soup.find_all('div', class_=re.compile(r'card|event')) 
    
    for card in cards:
        text = card.get_text(strip=True)
        if "Sadler's Wells East" not in text and "The Dance Floor" not in text:
            continue
            
        title_tag = card.find(re.compile(r'h[2-4]'))
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # STRICT Filtering for User Preferences
        t_low = title.lower()
        if 'production' in t_low or 'ticketed' in t_low:
            # Likely a paid show, user prefers public/community stuff here
            # User said "not necessarily related to dance"
            pass
            
        keywords = ['workshop', 'talk', 'social', 'free', 'class', 'community', 'floor']
        if not any(k in t_low for k in keywords):
            continue

        # Ignore straight dance performances
        # User said "mostly dance events which can be ignored"
        if 'performance' in t_low and 'free' not in t_low:
            continue

        # Extract info
        link = card.find('a')
        event_url = url
        if link and link.get('href'):
            event_url = "https://www.sadlerswells.com" + link.get('href')
            
        date_raw = "See website"
        # Try to find date in card
        
        events.append({
            'title': title,
            'url': event_url,
            'description': "Community event at Sadler's Wells East.",
            'date_str': date_raw,
            'date_obj': None, # Needs parsing
            'category': 'Community',
            'sub_category': "Sadler's Wells",
            'price': "Check website",
            'source': "Sadler's Wells East"
        })
        
    return events
