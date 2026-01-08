import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_here_east_events():
    url = "https://hereeast.com/events/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Here East events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # Event tiles
    tiles = soup.find_all('h3', class_='EventTile__title')
    
    for title_tag in tiles:
        title = title_tag.get_text(strip=True).replace('.', '')
        
        container = title_tag.find_parent('a')
        event_url = url
        if container and container.get('href'):
            event_url = "https://hereeast.com" + container.get('href')
            
        parent = title_tag.parent
        date_raw = "See website"
        date_tag = parent.find('div', class_='EventTile__date')
        if date_tag:
            date_raw = date_tag.get_text(strip=True)

        date_obj = parse_event_date(date_raw) # Attempt fuzzy parse
        date_str = date_raw
        if date_obj:
            date_str = date_obj.strftime("%a, %d %b %Y")

        # Sub-category
        sub_cat = 'Tech/Innovation'
        if 'market' in title.lower(): sub_cat = 'Market'
        elif 'cinema' in title.lower(): sub_cat = 'Cinema'

        events.append({
            'title': title,
            'url': event_url,
            'description': "Event at Here East campus.",
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'STEM / Factual',
            'sub_category': sub_cat,
            'price': "Check website",
            'source': 'Here East'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_here_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
