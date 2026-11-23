import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_COMMUNITY,
    DATE_SEE_WEBSITE,
    HTML_PARSER,
    PRICE_CHECK_WEBSITE,
    SADLERS_BASE_URL,
    SADLERS_DESCRIPTION,
    SADLERS_EVENTS_URL,
    SADLERS_FREE_KEYWORD,
    SADLERS_PERFORMANCE_KEYWORD,
    SADLERS_TITLE_KEYWORDS,
    SADLERS_VENUE_TEXTS,
    SOURCE_SADLERS,
    SUB_SADLERS,
    USER_AGENT_BROWSER,
)

def fetch_sadlers_events():
    # Sadler's Wells East specific URL or search
    # Often they list community events separately.
    # Trying the main what's on with query for East
    url = SADLERS_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        # Sadler's might handle filters via JS. If so, we might need a broader scrape.
        # Fallback to main list and filter by text "Sadler's Wells East"
    except:
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []
    
    # This selector is a guess based on standard implementations, 
    # might need adjustment if I could see the HTML.
    # Assuming cards with titles.
    cards = soup.find_all('div', class_=re.compile(r'card|event')) 
    
    for card in cards:
        text = card.get_text(strip=True)
        if not any(v in text for v in SADLERS_VENUE_TEXTS):
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
            
        keywords = SADLERS_TITLE_KEYWORDS
        if not any(k in t_low for k in keywords):
            continue

        # Ignore straight dance performances
        # User said "mostly dance events which can be ignored"
        if SADLERS_PERFORMANCE_KEYWORD in t_low and SADLERS_FREE_KEYWORD not in t_low:
            continue

        # Extract info
        link = card.find('a')
        event_url = url
        if link and link.get('href'):
            event_url = SADLERS_BASE_URL + link.get('href')
            
        date_raw = DATE_SEE_WEBSITE
        # Try to find date in card
        
        events.append({
            'title': title,
            'url': event_url,
            'description': SADLERS_DESCRIPTION,
            'date_str': date_raw,
            'date_obj': None, # Needs parsing
            'category': CATEGORY_COMMUNITY,
            'sub_category': SUB_SADLERS,
            'price': PRICE_CHECK_WEBSITE,
            'source': SOURCE_SADLERS
        })
        
    return events
