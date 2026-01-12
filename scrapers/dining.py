import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime

def fetch_dining_news():
    """
    Fetches news about restaurant openings and offers in Stratford/Westfield via Google News RSS.
    """
    queries = [
        "Stratford London new restaurant",
        "Westfield Stratford City dining news",
        "Stratford E20 restaurant opening",
        "Stratford London food offers",
        "Westfield Stratford new opening"
    ]
    
    events = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    seen_titles = set()

    for q in queries:
        rss_url = f"https://news.google.com/rss/search?q={q.replace(' ', '+')}&hl=en-GB&gl=GB&ceid=GB:en"
        
        try:
            res = requests.get(rss_url, headers=headers, timeout=10)
            if res.status_code != 200: 
                continue
            
            # Google News RSS is XML
            try:
                root = ET.fromstring(res.content)
            except ET.ParseError:
                continue
            
            # Parse Items (Top 3 per query to avoid noise)
            for item in root.findall('.//item')[:3]: 
                title = item.find('title').text
                if title in seen_titles:
                    continue
                seen_titles.add(title)

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
                
                # Filter old news (older than 60 days - openings might be relevant for a while)
                if date_obj and (datetime.now() - date_obj).days > 60:
                    continue

                events.append({
                    'title': title,
                    'url': link,
                    'description': clean_desc,
                    'date_str': pubDate,
                    'date_obj': date_obj,
                    'category': 'Dining & Offers',
                    'sub_category': 'News & Openings',
                    'price': "-",
                    'source': 'Google News'
                })
                
        except Exception as e:
            print(f"Error fetching dining news for {q}: {e}")
            
    return events

if __name__ == "__main__":
    news = fetch_dining_news()
    for n in news:
        print(f"[{n['date_str']}] {n['title']}\n{n['url']}\n")
