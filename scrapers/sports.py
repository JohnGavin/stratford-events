import requests
from bs4 import BeautifulSoup
import re

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
            # Baller League is often football-based
            continue
            
        description_div = container.find('div', style=re.compile(r'max-height:75px'))
        description = description_div.get_text(strip=True) if description_div else ""
        
        if 'football' in description.lower():
            continue

        link_tag = container.find('a', string='Find out more')
        event_url = "https://copperboxarena.org.uk" + link_tag.get('href') if link_tag else url
        
        # Date is in the text nodes of the div containing the title
        content_div = title_tag.parent
        date_str = "See website"
        # The date is usually after the title in the text
        text_content = content_div.get_text(" | ", strip=True)
        # Try to extract date like "Jan 11, 2026"
        date_match = re.search(r'([A-Z][a-z]{2}\s\d{1,2},\s\d{4})', text_content)
        if date_match:
            date_str = date_match.group(1)

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'category': 'Sports',
            'source': 'Copper Box Arena'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_copper_box_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
