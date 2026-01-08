import requests
import json
from datetime import datetime

def fetch_ucl_events():
    # Funnelback API for UCL East events
    url = "https://cms-feed.ucl.ac.uk/s/search.json?collection=drupal-meta-events&meta_UclOrgUnit=%22UCL+East%22"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching UCL events: {e}")
        return []

    events = []
    results = data.get('response', {}).get('resultPacket', {}).get('results', [])
    
    for res in results:
        meta = res.get('metaData', {})
        
        # Filter for science/STEM related tags if possible, 
        # but the request was for science/STEM factual stuff.
        # Most UCL East events fit this better than general ones.
        
        title = res.get('title', '')
        summary = res.get('summary', '')
        
        # Filter out Dance/Musicals
        if any(word in title.lower() or word in summary.lower() for word in ['dance', 'musical', 'ballet', 'opera']):
            continue
            
        event = {
            'title': title,
            'url': res.get('liveUrl', ''),
            'description': summary,
            'date_str': meta.get('UclEventStartDate', 'See website'),
            'location': meta.get('UclEventLocation', 'UCL East'),
            'category': 'STEM/Factual',
            'source': 'UCL East'
        }
        events.append(event)
        
    return events

if __name__ == "__main__":
    events = fetch_ucl_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
