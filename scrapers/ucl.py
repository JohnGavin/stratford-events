import requests
import json
from datetime import datetime
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_STEM,
    DATE_SEE_WEBSITE,
    DISPLAY_DATE_FORMAT,
    DISPLAY_TIME_SUFFIX_FORMAT,
    SOURCE_UCL,
    SUB_GENERAL,
    UCL_EVENTS_URL,
    UCL_FORBIDDEN_KEYWORDS,
    UCL_PRICE,
    UCL_PUBLIC_AUDIENCE_KEYWORDS,
    UCL_RESTRICTED_AUDIENCE_KEYWORDS,
    UCL_SUBCATEGORY_RULES,
    USER_AGENT_BROWSER,
)

def fetch_ucl_events():
    # Funnelback API for UCL East events
    # We can try to filter by audience in the query if possible, but easier to post-filter
    url = UCL_EVENTS_URL
    
    headers = {
        "User-Agent": USER_AGENT_BROWSER
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
        if not any(k in audience for k in UCL_PUBLIC_AUDIENCE_KEYWORDS):
            # Some events might not strictly tag 'public' but are. 
            # If strictly 'students only' or 'staff only', exclude.
            if any(k in audience for k in UCL_RESTRICTED_AUDIENCE_KEYWORDS):
                continue

        title = res.get('title', '')
        summary = res.get('summary', '')
        
        # Filter out Dance/Musicals
        if any(word in title.lower() or word in summary.lower() for word in UCL_FORBIDDEN_KEYWORDS):
            continue
            
        # 2. Sub-categorization
        sub_cat = SUB_GENERAL
        t_low = title.lower()
        for rule_sub_cat, rule_keywords in UCL_SUBCATEGORY_RULES:
            if any(k in t_low for k in rule_keywords):
                sub_cat = rule_sub_cat
                break
            
        # 3. Date Parsing
        date_raw = meta.get('UclEventStartDate', '')
        date_obj = None
        date_str = DATE_SEE_WEBSITE
        if date_raw:
            try:
                date_obj = datetime.fromisoformat(date_raw)
                date_str = date_obj.strftime(DISPLAY_DATE_FORMAT + DISPLAY_TIME_SUFFIX_FORMAT)
            except ValueError:
                date_str = date_raw

        # 4. Price
        # UCL API often puts price in a specific field or text. 
        # Using a default 'Free/Check' if not found. 
        # Most public UCL events are free.
        price_str = UCL_PRICE
        
        event = {
            'title': title,
            'url': res.get('liveUrl', ''),
            'description': summary, # Funnelback summary is usually a good snippet
            'date_str': date_str,
            'date_obj': date_obj,
            'location': meta.get('UclEventLocation', SOURCE_UCL),
            'category': CATEGORY_STEM,
            'sub_category': sub_cat,
            'price': price_str,
            'source': SOURCE_UCL
        }
        events.append(event)
        
    return events

if __name__ == "__main__":
    events = fetch_ucl_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
