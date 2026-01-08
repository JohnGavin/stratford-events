import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_stratford_east_events():
    url = "https://www.stratfordeast.com/whats-on"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Stratford East events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    titles = soup.find_all('h2')
    
    for title_tag in titles:
        link_tag = title_tag.find('a')
        if not link_tag:
            continue
            
        title = link_tag.get_text(strip=True)
        event_url = "https://www.stratfordeast.com" + link_tag.get('href')
        
        container = title_tag.parent.parent
        
        date_div = container.find('div', class_='postDate_l')
        date_raw = date_div.get_text(strip=True) if date_div else ""
        
        # Parse start date
        date_obj = None
        date_str = date_raw
        if date_raw:
            # Usually "SAT 31 JAN 2026 - ..."
            # Take the first date part
            first_date = date_raw.split('-')[0].strip()
            try:
                date_obj = datetime.strptime(first_date, "%a %d %b %Y")
                date_str = date_obj.strftime("%a, %d %b %Y")
            except:
                pass
        
        desc_p = container.find('p')
        description = desc_p.get_text(strip=True) if desc_p else ""
        
        forbidden = ['musical', 'dance', 'pantomime', 'panto', 'concert', 'music of']
        if any(word in title.lower() or word in description.lower() for word in forbidden):
            continue
            
        # Price extraction (often not on listing page, assume paid)
        price_str = "Check website"

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Theatre',
            'sub_category': 'Stratford East',
            'price': price_str,
            'source': 'Stratford East'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_stratford_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
