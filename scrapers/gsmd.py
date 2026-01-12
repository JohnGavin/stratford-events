import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_gsmd_events():
    url = "https://www.gsmd.ac.uk/whats-on"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching GSMD events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # GSMD listing structure (usually cards)
    # Generic look for articles or cards
    cards = soup.find_all('article')
    if not cards:
        cards = soup.find_all('div', class_=re.compile(r'card|listing'))

    for card in cards:
        # Title
        title_tag = card.find(re.compile(r'h[2-4]'))
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        # Link
        link_tag = card.find('a')
        if not link_tag: continue
        href = link_tag.get('href')
        if href.startswith('/'): href = "https://www.gsmd.ac.uk" + href
        event_url = href
        
        # We need to filter for LOCATION = Stratford/East
        # Usually location is on the listing, but might need deep scrape.
        # Let's check listing text first.
        card_text = card.get_text(strip=True)
        
        # Initial Location Check
        # GSMD is mostly Barbican. We strictly want E15/E20.
        # Keywords: "East", "Stratford", "Elizabeth Park"
        is_east = False
        if any(x in card_text for x in ['Stratford', 'East Bank', 'Olympic Park']):
            is_east = True
        
        # Deep Scrape for details & location confirmation
        description = ""
        date_raw = "See website"
        price_str = "Check website"
        duration = ""
        location = "Unknown"
        
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, 'html.parser')
            
            # Location check in detail page
            # Look for "Venue" or "Location" label
            body_text = soup_d.get_text()
            if not is_east:
                # Double check detail page
                if any(x in body_text for x in ['Stratford', 'East Bank', 'Olympic Park']):
                    is_east = True
            
            if not is_east:
                continue # Skip if not an East event

            # Extract details
            # Date
            date_tag = soup_d.find('time')
            if date_tag: date_raw = date_tag.get_text(strip=True)
            
            # Price
            price_str = normalize_price(body_text)
            
            # Duration
            if "Duration" in body_text:
                # Simple extraction guess
                # Find the word and grab next few words
                pass
            
            # Summary
            intro = soup_d.find('div', class_=re.compile(r'intro|summary'))
            if intro: description = intro.get_text(strip=True)
            else:
                p = soup_d.find('p')
                if p: description = p.get_text(strip=True)

        except:
            pass
            
        if not is_east: continue

        date_obj = parse_event_date(date_raw)
        
        # 14-Day Filter (User Request)
        if date_obj:
            now = datetime.now()
            # Handle potential timezone mismatch
            if date_obj.tzinfo is None and now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            elif date_obj.tzinfo is not None and now.tzinfo is None:
                now = now.astimezone()
                
            delta = date_obj - now
            if delta.days > 14:
                continue
        
        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': 'Theatre', # GSMD is mostly drama/music
            'sub_category': 'GSMD East',
            'price': price_str,
            'source': 'Guildhall School'
        })
        
    return events
