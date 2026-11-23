import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_STEM,
    DATE_SEE_WEBSITE,
    HERE_EAST_BASE_URL,
    HERE_EAST_DEFAULT_SUBCATEGORY,
    HERE_EAST_ERROR_DESCRIPTION,
    HERE_EAST_EVENTS_URL,
    HERE_EAST_MIN_DESCRIPTION_CHARS,
    HERE_EAST_SUBCATEGORY_KEYWORDS,
    HTML_PARSER,
    PRICE_CHECK_WEBSITE,
    PRICE_FREE,
    SOURCE_HERE_EAST,
    USER_AGENT_BROWSER,
)

def fetch_here_east_events():
    url = HERE_EAST_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Here East events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []
    
    tiles = soup.find_all('h3', class_='EventTile__title')
    
    for title_tag in tiles:
        title = title_tag.get_text(strip=True).replace('.', '')
        
        container = title_tag.find_parent('a')
        event_url = url
        if container and container.get('href'):
            event_url = HERE_EAST_BASE_URL + container.get('href')
            
        # Deep Scrape
        try:
            res_detail = requests.get(event_url, headers=headers)
            soup_detail = BeautifulSoup(res_detail.text, HTML_PARSER)
            
            # Summary - usually in first paragraph of content
            # Inspect structure on page... usually 'ContentBlock' or similar
            description = ""
            desc_tag = soup_detail.find('div', class_='RichText') 
            if desc_tag:
                # Get first decent paragraph
                for p in desc_tag.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > HERE_EAST_MIN_DESCRIPTION_CHARS:
                        description = text
                        break
            
            # Date
            date_raw = DATE_SEE_WEBSITE
            # Here East detail pages often have a specific date block
            # Fallback to the list page date if needed, but detail is better
            # Let's assume list page date was 'EventTile__date'
            
            # Price
            # Look for "Price" or "£" in text
            price_str = PRICE_CHECK_WEBSITE
            body_text = soup_detail.get_text()
            if '£' in body_text:
                price_str = normalize_price(body_text)
            elif PRICE_FREE in body_text:
                price_str = PRICE_FREE
                
            # Date from list page is often easiest/safest as fallback
            # but let's re-parse
            date_tag = title_tag.parent.find('div', class_='EventTile__date')
            if date_tag:
                date_raw = date_tag.get_text(strip=True)

        except Exception as e:
            print(f"Error scraping detail {event_url}: {e}")
            description = HERE_EAST_ERROR_DESCRIPTION
            date_raw = DATE_SEE_WEBSITE
            price_str = PRICE_CHECK_WEBSITE

        date_obj = parse_event_date(date_raw)
        
        # Mandatory Date check logic happens in main.py, but we try our best here
        
        sub_cat = HERE_EAST_DEFAULT_SUBCATEGORY
        for keyword, label in HERE_EAST_SUBCATEGORY_KEYWORDS:
            if keyword in title.lower():
                sub_cat = label
                break

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': CATEGORY_STEM,
            'sub_category': sub_cat,
            'price': price_str,
            'source': SOURCE_HERE_EAST
        })
        
    return events

if __name__ == "__main__":
    events = fetch_here_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
