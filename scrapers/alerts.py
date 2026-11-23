import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from utils.common import parse_event_date
from params import (
    ALERTS_MAX_AGE_DAYS,
    ALERTS_QUERIES,
    CATEGORY_NEWS,
    GOOGLE_NEWS_RSS_URL_TEMPLATE,
    HTTP_STATUS_OK,
    NEWS_ITEMS_PER_QUERY,
    NEWS_PUBDATE_FORMAT,
    PRICE_NONE,
    SOURCE_GOOGLE_NEWS,
    SUB_GOOGLE_ALERTS,
    USER_AGENT_BROWSER,
)

def fetch_google_alerts():
    # RSS Feeds for keywords
    queries = ALERTS_QUERIES
    
    events = []
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }

    for q in queries:
        rss_url = GOOGLE_NEWS_RSS_URL_TEMPLATE.format(query=q.replace(' ', '+'))
        
        try:
            res = requests.get(rss_url, headers=headers)
            if res.status_code != HTTP_STATUS_OK: continue
            
            root = ET.fromstring(res.content)
            
            # Parse Items
            for item in root.findall('.//item')[:NEWS_ITEMS_PER_QUERY]: # Top hits per query
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
                    date_obj = datetime.strptime(pubDate, NEWS_PUBDATE_FORMAT)
                except:
                    pass
                
                # Filter old news (older than ALERTS_MAX_AGE_DAYS)
                if date_obj and (datetime.now() - date_obj).days > ALERTS_MAX_AGE_DAYS:
                    continue

                events.append({
                    'title': title,
                    'url': link,
                    'description': clean_desc,
                    'date_str': pubDate,
                    'date_obj': date_obj,
                    'category': CATEGORY_NEWS,
                    'sub_category': SUB_GOOGLE_ALERTS,
                    'price': PRICE_NONE,
                    'source': SOURCE_GOOGLE_NEWS
                })
                
        except Exception as e:
            print(f"Error fetching alerts for {q}: {e}")
            
    return events

# Need regex for cleanup
import re
