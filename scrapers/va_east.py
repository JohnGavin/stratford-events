import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_va_events():
    # V&A uses a filtered URL or we can scrape the main list and filter by venue attribute
    url = "https://www.vam.ac.uk/whatson?venue=east-storehouse&venue=east-museum"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching V&A events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
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
        if 'East' not in venue_text and 'Storehouse' not in venue_text:
            if not item.has_attr('data-wo-venue'):
                continue
                
        title_tag = item.find('h3')
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        link = item.find('a')
        event_url = url
        if link and link.get('href'):
            event_url = link.get('href')
            if event_url.startswith('/'): event_url = "https://www.vam.ac.uk" + event_url

        # Deep scrape for details
        description = ""
        date_raw = "See website"
        price_str = "Check website"
        
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, 'html.parser')
            
            # Summary
            intro = soup_d.find('div', class_='b-text-intro')
            if intro: description = intro.get_text(strip=True)
            else:
                p = soup_d.find('p')
                if p: description = p.get_text(strip=True)[:300]

            # Date
            # Usually in a header or info block
            date_info = soup_d.find(class_=re.compile(r'date|time'))
            if date_info: date_raw = date_info.get_text(strip=True)
            
            # Price
            if 'Free' in soup_d.get_text(): price_str = "Free"
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
            'category': 'STEM / Factual',
            'sub_category': 'Museum / Exhibition',
            'price': price_str,
            'source': 'V&A East'
        })
        
    return events
