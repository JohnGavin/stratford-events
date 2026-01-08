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
    
    tiles = soup.find_all('h3', class_='EventTile__title')
    
    for title_tag in tiles:
        title = title_tag.get_text(strip=True).replace('.', '')
        
        container = title_tag.find_parent('a')
        event_url = url
        if container and container.get('href'):
            event_url = "https://hereeast.com" + container.get('href')
            
        # Deep Scrape
        try:
            res_detail = requests.get(event_url, headers=headers)
            soup_detail = BeautifulSoup(res_detail.text, 'html.parser')
            
            # Summary - usually in first paragraph of content
            # Inspect structure on page... usually 'ContentBlock' or similar
            description = ""
            desc_tag = soup_detail.find('div', class_='RichText') 
            if desc_tag:
                # Get first decent paragraph
                for p in desc_tag.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        description = text
                        break
            
            # Date
            date_raw = "See website"
            # Here East detail pages often have a specific date block
            # Fallback to the list page date if needed, but detail is better
            # Let's assume list page date was 'EventTile__date'
            
            # Price
            # Look for "Price" or "£" in text
            price_str = "Check website"
            body_text = soup_detail.get_text()
            if '£' in body_text:
                price_str = normalize_price(body_text)
            elif 'Free' in body_text:
                price_str = "Free"
                
            # Date from list page is often easiest/safest as fallback
            # but let's re-parse
            date_tag = title_tag.parent.find('div', class_='EventTile__date')
            if date_tag:
                date_raw = date_tag.get_text(strip=True)

        except Exception as e:
            print(f"Error scraping detail {event_url}: {e}")
            description = "Click link for details."
            date_raw = "See website"
            price_str = "Check website"

        date_obj = parse_event_date(date_raw)
        
        # Mandatory Date check logic happens in main.py, but we try our best here
        
        sub_cat = 'Tech/Innovation'
        if 'market' in title.lower(): sub_cat = 'Market'
        elif 'cinema' in title.lower(): sub_cat = 'Cinema'

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': 'STEM / Factual',
            'sub_category': sub_cat,
            'price': price_str,
            'source': 'Here East'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_here_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
