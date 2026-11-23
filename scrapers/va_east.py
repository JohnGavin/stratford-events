import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_STEM,
    DATE_SEE_WEBSITE,
    DESCRIPTION_MAX_CHARS,
    HTML_PARSER,
    PRICE_CHECK_WEBSITE,
    PRICE_FREE,
    SOURCE_VA,
    SUB_MUSEUM,
    USER_AGENT_BROWSER,
    VA_BASE_URL,
    VA_EVENTS_URL,
    VA_VENUE_TEXTS,
)

def fetch_va_events():
    # V&A uses a filtered URL or we can scrape the main list and filter by venue attribute
    url = VA_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching V&A events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []
    
    # Items usually in b-card or similar
    # Based on grep: data-wo-venue="east-storehouse"
    
    items = soup.find_all('li', attrs={'data-wo-venue': re.compile(r'east-')})
    
    if not items:
        # Fallback: try finding all cards and checking text
        items = soup.find_all('div', class_='b-card')

    for item in items:
        # Venue check if scraping main list
        venue_tag = item.find(class_=re.compile(r'venue'))
        venue_text = venue_tag.get_text(strip=True) if venue_tag else ""
        if not any(v in venue_text for v in VA_VENUE_TEXTS):
            if not item.has_attr('data-wo-venue'):
                continue
                
        title_tag = item.find('h3')
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        link = item.find('a')
        event_url = url
        if link and link.get('href'):
            event_url = link.get('href')
            if event_url.startswith('/'): event_url = VA_BASE_URL + event_url

        # Deep scrape for details
        description = ""
        date_raw = DATE_SEE_WEBSITE
        price_str = PRICE_CHECK_WEBSITE
        
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, HTML_PARSER)
            
            # Summary
            intro = soup_d.find('div', class_='b-text-intro')
            if intro: description = intro.get_text(strip=True)
            else:
                p = soup_d.find('p')
                if p: description = p.get_text(strip=True)[:DESCRIPTION_MAX_CHARS]

            # Date
            # Usually in a header or info block
            date_info = soup_d.find(class_=re.compile(r'date|time'))
            if date_info: date_raw = date_info.get_text(strip=True)
            
            # Price
            if PRICE_FREE in soup_d.get_text(): price_str = PRICE_FREE
            else: price_str = normalize_price(soup_d.get_text())
            
        except:
            pass
            
        date_obj = parse_event_date(date_raw)
        
        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': CATEGORY_STEM,
            'sub_category': SUB_MUSEUM,
            'price': price_str,
            'source': SOURCE_VA
        })
        
    return events
