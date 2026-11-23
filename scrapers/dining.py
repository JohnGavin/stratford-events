import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from params import (
    CATEGORY_DINING,
    DINING_GENERIC_KEYWORDS,
    DINING_HTTP_TIMEOUT_SECONDS,
    DINING_MAX_AGE_DAYS,
    DINING_QUERIES,
    DINING_STRATFORD_KEYWORDS,
    GOOGLE_NEWS_RSS_URL_TEMPLATE,
    HTTP_STATUS_OK,
    NEWS_ITEMS_PER_QUERY,
    NEWS_PUBDATE_FORMAT,
    PRICE_NONE,
    SOURCE_GOOGLE_NEWS,
    SUB_DINING_NEWS,
    USER_AGENT_BROWSER,
)

def fetch_dining_news():
    """
    Fetches news about restaurant openings and offers in Stratford/Westfield via Google News RSS.
    """
    queries = DINING_QUERIES
    
    events = []
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }

    seen_titles = set()

    for q in queries:
        rss_url = GOOGLE_NEWS_RSS_URL_TEMPLATE.format(query=q.replace(' ', '+'))
        
        try:
            res = requests.get(rss_url, headers=headers, timeout=DINING_HTTP_TIMEOUT_SECONDS)
            if res.status_code != HTTP_STATUS_OK: 
                continue
            
            # Google News RSS is XML
            try:
                root = ET.fromstring(res.content)
            except ET.ParseError:
                continue
            
            # Parse Items (top hits per query to avoid noise)
            for item in root.findall('.//item')[:NEWS_ITEMS_PER_QUERY]: 
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
                    date_obj = datetime.strptime(pubDate, NEWS_PUBDATE_FORMAT)
                except:
                    pass
                
                # Filter old news (older than DINING_MAX_AGE_DAYS - openings might be relevant for a while)
                if date_obj and (datetime.now() - date_obj).days > DINING_MAX_AGE_DAYS:
                    continue

                # Filter generic London-wide articles - only keep Stratford-specific
                combined_text = (title + " " + clean_desc).lower()
                stratford_keywords = DINING_STRATFORD_KEYWORDS
                generic_keywords = DINING_GENERIC_KEYWORDS
                # Skip if it matches generic patterns
                if any(g in combined_text for g in generic_keywords):
                    continue
                # Skip if no Stratford-specific keyword is found
                if not any(s in combined_text for s in stratford_keywords):
                    continue

                events.append({
                    'title': title,
                    'url': link,
                    'description': clean_desc,
                    'date_str': pubDate,
                    'date_obj': date_obj,
                    'category': CATEGORY_DINING,
                    'sub_category': SUB_DINING_NEWS,
                    'price': PRICE_NONE,
                    'source': SOURCE_GOOGLE_NEWS
                })
                
        except Exception as e:
            print(f"Error fetching dining news for {q}: {e}")
            
    return events

if __name__ == "__main__":
    news = fetch_dining_news()
    for n in news:
        print(f"[{n['date_str']}] {n['title']}\n{n['url']}\n")
