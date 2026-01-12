import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_barbican_events():
    url = "https://www.barbican.org.uk/whats-on"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Barbican events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    articles = soup.find_all('article', class_='listing--event')
    
    for art in articles:
        # Title
        title_tag = art.find('h2', class_='listing-title')
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # Link
        link_tag = art.find('a', class_='search-listing__link')
        event_url = url
        if link_tag and link_tag.get('href'):
            event_url = "https://www.barbican.org.uk" + link_tag.get('href')
            
        # Description
        description = ""
        desc_div = art.find(class_='search-listing__intro')
        if desc_div:
            description = desc_div.get_text(strip=True)

        # Deep Scrape for Date & Price
        date_raw = "See website"
        price_str = "Check website"
        date_obj = None
        
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, 'html.parser')
            
            # Date: Look for date block
            # Barbican detail pages usually have a hero block with date
            # common classes: 'hero-header__date', 'event-detail__date'
            date_tag = soup_d.find(class_=re.compile(r'date|time'))
            if date_tag:
                date_raw = date_tag.get_text(strip=True)
            else:
                # Try finding text with 2025/2026
                pass
                
            # Price
            price_tag = soup_d.find(string=re.compile(r'£'))
            if price_tag:
                price_str = normalize_price(price_tag)
                
        except:
            pass
            
        date_obj = parse_event_date(date_raw)
        
        # 14-Day Filter
        if date_obj:
            now = datetime.now()
            # Handle potential timezone mismatch
            if date_obj.tzinfo is None and now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            elif date_obj.tzinfo is not None and now.tzinfo is None:
                now = now.astimezone()
                
            delta = date_obj - now
            # Filter if > 14 days in future
            if delta.days > 14:
                continue
                
        # If no date found, we might keep it or drop it. 
        # Main.py drops events without date_obj. 
        # So we must parse a date. If we can't, it will be dropped anyway.

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': 'Theatre', # Barbican is mostly Arts/Theatre/Music
            'sub_category': 'Barbican Centre',
            'price': price_str,
            'source': 'Barbican'
        })
        
    return events
