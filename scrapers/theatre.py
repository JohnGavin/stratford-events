import requests
from bs4 import BeautifulSoup

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
    
    # Each show is in a div with class listPostContent or similar
    # Based on grep, it seems they are in containers. 
    # Let's find h2 and go up/down
    titles = soup.find_all('h2')
    
    for title_tag in titles:
        link_tag = title_tag.find('a')
        if not link_tag:
            continue
            
        title = link_tag.get_text(strip=True)
        event_url = "https://www.stratfordeast.com" + link_tag.get('href')
        
        # Parent or sibling container
        container = title_tag.parent.parent
        
        date_div = container.find('div', class_='postDate_l')
        date_str = date_div.get_text(strip=True) if date_div else "See website"
        
        desc_p = container.find('p')
        description = desc_p.get_text(strip=True) if desc_p else ""
        
        # Filter: No Musicals or Dance
        # Note: "Robin Hood and the Merry Mandem" is a Panto, usually musical.
        # "Legend - Music of Bob Marley" is definitely musical.
        # "The Cavern Club Story" likely musical.
        
        forbidden = ['musical', 'dance', 'pantomime', 'panto', 'concert', 'music of']
        if any(word in title.lower() or word in description.lower() for word in forbidden):
            continue
            
        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'category': 'Theatre',
            'source': 'Stratford East'
        })
        
    return events

if __name__ == "__main__":
    events = fetch_stratford_east_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
