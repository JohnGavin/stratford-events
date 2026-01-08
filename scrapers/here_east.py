import requests
from bs4 import BeautifulSoup

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
        
        # Link is usually in an ancestor
        container = title_tag.find_parent('a')
        event_url = url
        if container and container.get('href'):
            event_url = "https://hereeast.com" + container.get('href')
            
        # Try to find date in siblings or parent
        # Based on typical Here East structure
        parent = title_tag.parent
        date_str = "See website"
        date_tag = parent.find('div', class_='EventTile__date')
        if date_tag:
            date_str = date_tag.get_text(strip=True)

        events.append({
            'title': title,
            'url': event_url,
            'description': '',
            'date_str': date_str,
            'category': 'Tech/Innovation',
            'source': 'Here East'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_here_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
