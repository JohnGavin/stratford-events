import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from utils.common import parse_event_date

def fetch_google_alerts():
    # RSS Feeds for keywords
    queries = [
        "Stratford London events",
        "Queen Elizabeth Olympic Park news",
        "UCL East events",
        "East Bank Stratford"
    ]
    
    events = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for q in queries:
        rss_url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-GB&gl=GB&ceid=GB:en"
        
        try:
            res = requests.get(rss_url, headers=headers)
            if res.status_code != 200: continue
            
            root = ET.fromstring(res.content)
            
            # Parse Items
            for item in root.findall('.//item')[:3]: # Top 3 per query
                title = item.find('title').text
                link = item.find('link').text
                pubDate = item.find('pubDate').text
                description = item.find('description').text # HTML snippet usually
                
                # Clean description (remove HTML tags if any)
                clean_desc = re.sub('<[^<]+?>', '', description) if description else ""
                
                # Date parsing
                # RFC 822 format: "Mon, 08 Jan 2026 12:00:00 GMT"
                date_obj = None
                try:
                    date_obj = datetime.strptime(pubDate, "%a, %d %b %Y %H:%M:%S %Z")
                except:
                    pass
                
                # Filter old news (older than 30 days)
                if date_obj and (datetime.now() - date_obj).days > 30:
                    continue

                events.append({
                    'title': title,
                    'url': link,
                    'description': clean_desc,
                    'date_str': pubDate,
                    'date_obj': date_obj,
                    'category': 'News & Alerts',
                    'sub_category': 'Google Alerts',
                    'price': "-",
                    'source': 'Google News'
                })
                
        except Exception as e:
            print(f"Error fetching alerts for {q}: {e}")
            
    return events

# Need regex for cleanup
import re
