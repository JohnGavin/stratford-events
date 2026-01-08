import requests
import json
from datetime import datetime
from utils.common import parse_event_date, normalize_price

def fetch_ucl_events():
    # Funnelback API for UCL East events
    # We can try to filter by audience in the query if possible, but easier to post-filter
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
        
        # 1. Public Filter
        # Check 'UclEventAudience'
        audience = meta.get('UclEventAudience', '').lower()
        if 'public' not in audience and 'everyone' not in audience:
            # Some events might not strictly tag 'public' but are. 
            # If strictly 'students only' or 'staff only', exclude.
            if 'staff' in audience or 'student' in audience:
                continue

        title = res.get('title', '')
        summary = res.get('summary', '')
        
        # Filter out Dance/Musicals
        if any(word in title.lower() or word in summary.lower() for word in ['dance', 'musical', 'ballet', 'opera']):
            continue
            
        # 2. Sub-categorization
        sub_cat = 'General'
        t_low = title.lower()
        if 'cinema' in t_low or 'screening' in t_low or 'film' in t_low:
            sub_cat = 'Cinema'
        elif 'exhibition' in t_low or 'gallery' in t_low:
            sub_cat = 'Exhibition'
        elif 'lecture' in t_low or 'talk' in t_low or 'conversation' in t_low:
            sub_cat = 'Lecture/Talk'
            
        # 3. Date Parsing
        date_raw = meta.get('UclEventStartDate', '')
        date_obj = None
        date_str = 'See website'
        if date_raw:
            try:
                date_obj = datetime.fromisoformat(date_raw)
                date_str = date_obj.strftime("%a, %d %b %Y @ %H:%M")
            except ValueError:
                date_str = date_raw

        # 4. Price
        # UCL API often puts price in a specific field or text. 
        # Using a default 'Free/Check' if not found. 
        # Most public UCL events are free.
        price_str = "Free (usually)"
        
        event = {
            'title': title,
            'url': res.get('liveUrl', ''),
            'description': summary, # Funnelback summary is usually a good snippet
            'date_str': date_str,
            'date_obj': date_obj,
            'location': meta.get('UclEventLocation', 'UCL East'),
            'category': 'STEM / Factual',
            'sub_category': sub_cat,
            'price': price_str,
            'source': 'UCL East'
        }
        events.append(event)
        
    return events

if __name__ == "__main__":
    events = fetch_ucl_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
