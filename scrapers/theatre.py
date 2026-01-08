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
        
        # Shallow data
        container = title_tag.parent.parent
        date_div = container.find('div', class_='postDate_l')
        date_raw = date_div.get_text(strip=True) if date_div else ""
        
        # Deep Scrape
        description = ""
        duration = ""
        price_str = "Check website"
        times = []
        
        try:
            res_detail = requests.get(event_url, headers=headers)
            soup_detail = BeautifulSoup(res_detail.text, 'html.parser')
            
            # Full Description
            # Usually in a 'production-content' or similar div
            content_div = soup_detail.find('div', class_='production-content')
            if content_div:
                description = content_div.get_text(strip=True)[:300] + "..." # Limit length but keep enough
            else:
                # Fallback to meta description
                meta = soup_detail.find('meta', attrs={'name': 'description'})
                if meta: description = meta['content']

            # Price extraction from sidebar/booking info
            # Look for £
            page_text = soup_detail.get_text()
            price_str = normalize_price(page_text)
            
            # Duration & Times
            # Often labelled "Running Time"
            if "Running Time" in page_text:
                # Regex or text search nearby
                pass # Complex without seeing HTML structure
                
        except Exception as e:
            print(f"Error scraping theatre detail {event_url}: {e}")

        # Parse start date
        date_obj = None
        date_str = date_raw
        if date_raw:
            # Usually "SAT 31 JAN 2026 - ..."
            first_date = date_raw.split('-')[0].strip()
            try:
                date_obj = datetime.strptime(first_date, "%a %d %b %Y")
                date_str = date_obj.strftime("%a, %d %b %Y")
            except:
                pass
        
        forbidden = ['musical', 'dance', 'pantomime', 'panto', 'concert', 'music of']
        if any(word in title.lower() or word in description.lower() for word in forbidden):
            continue

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
