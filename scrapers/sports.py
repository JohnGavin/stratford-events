import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_copper_box_events():
    url = "https://copperboxarena.org.uk/events"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Copper Box events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []
    
    # Each event is in a news-single container
    containers = soup.find_all('div', class_='news-single')
    
    for container in containers:
        title_tag = container.find('h2')
        if not title_tag:
            continue
            
        title = title_tag.get_text(strip=True)
        
        # Filter: No Football
        if 'football' in title.lower() or 'baller league' in title.lower():
            continue
            
        description_div = container.find('div', style=re.compile(r'max-height:75px'))
        description = description_div.get_text(strip=True) if description_div else ""
        
        if 'football' in description.lower():
            continue

        link_tag = container.find('a', string='Find out more')
        event_url = "https://copperboxarena.org.uk" + link_tag.get('href') if link_tag else url
        
        # Date Logic
        content_div = title_tag.parent
        date_str = "See website"
        date_obj = None
        
        text_content = content_div.get_text(" | ", strip=True)
        date_match = re.search(r'([A-Z][a-z]{2}\s\d{1,2},\s\d{4})', text_content)
        if date_match:
            raw_date = date_match.group(1)
            date_obj = datetime.strptime(raw_date, "%b %d, %Y")
            date_str = date_obj.strftime("%a, %d %b %Y")

        # Sub-category
        t_low = title.lower()
        sub_cat = 'General Sport'
        if 'basketball' in t_low or 'lions' in t_low:
            sub_cat = 'Basketball'
        elif 'netball' in t_low or 'pulse' in t_low:
            sub_cat = 'Netball'
        elif 'boxing' in t_low or 'fight' in t_low:
            sub_cat = 'Boxing'

        # Price (This site usually requires clicking through, so default to Check Website)
        price_str = "Check website"

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': 'Sports',
            'sub_category': sub_cat,
            'price': price_str,
            'source': 'Copper Box Arena'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_copper_box_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
