import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_SPORTS,
    COPPER_BOX_BASE_URL,
    COPPER_BOX_BASKETBALL_KEYWORDS,
    COPPER_BOX_BOXING_KEYWORDS,
    COPPER_BOX_DATE_FORMAT,
    COPPER_BOX_EVENTS_URL,
    COPPER_BOX_EXCLUDED_DESCRIPTION_KEYWORDS,
    COPPER_BOX_EXCLUDED_TITLE_KEYWORDS,
    COPPER_BOX_NETBALL_KEYWORDS,
    DATE_SEE_WEBSITE,
    DISPLAY_DATE_FORMAT,
    HTML_PARSER,
    PRICE_CHECK_WEBSITE,
    SOURCE_COPPER_BOX,
    SUB_BASKETBALL,
    SUB_BOXING,
    SUB_GENERAL_SPORT,
    SUB_NETBALL,
    USER_AGENT_BROWSER,
)

def fetch_copper_box_events():
    url = COPPER_BOX_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching Copper Box events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []
    
    # Each event is in a news-single container
    containers = soup.find_all('div', class_='news-single')
    
    for container in containers:
        title_tag = container.find('h2')
        if not title_tag:
            continue
            
        title = title_tag.get_text(strip=True)
        
        # Filter: No Football or Netball
        t_low = title.lower()
        if any(k in t_low for k in COPPER_BOX_EXCLUDED_TITLE_KEYWORDS):
            continue
            
        description_div = container.find('div', style=re.compile(r'max-height:75px'))
        description = description_div.get_text(strip=True) if description_div else ""
        
        if any(k in description.lower() for k in COPPER_BOX_EXCLUDED_DESCRIPTION_KEYWORDS):
            continue

        link_tag = container.find('a', string='Find out more')
        event_url = COPPER_BOX_BASE_URL + link_tag.get('href') if link_tag else url
        
        # Date Logic
        content_div = title_tag.parent
        date_str = DATE_SEE_WEBSITE
        date_obj = None
        
        text_content = content_div.get_text(" | ", strip=True)
        date_match = re.search(r'([A-Z][a-z]{2}\s\d{1,2},\s\d{4})', text_content)
        if date_match:
            raw_date = date_match.group(1)
            date_obj = datetime.strptime(raw_date, COPPER_BOX_DATE_FORMAT)
            date_str = date_obj.strftime(DISPLAY_DATE_FORMAT)

        # Sub-category
        t_low = title.lower()
        sub_cat = SUB_GENERAL_SPORT
        if any(k in t_low for k in COPPER_BOX_BASKETBALL_KEYWORDS):
            sub_cat = SUB_BASKETBALL
        elif any(k in t_low for k in COPPER_BOX_NETBALL_KEYWORDS):
            sub_cat = SUB_NETBALL
        elif any(k in t_low for k in COPPER_BOX_BOXING_KEYWORDS):
            sub_cat = SUB_BOXING

        # Price (This site usually requires clicking through, so default to Check Website)
        price_str = PRICE_CHECK_WEBSITE

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_str,
            'date_obj': date_obj,
            'category': CATEGORY_SPORTS,
            'sub_category': sub_cat,
            'price': price_str,
            'source': SOURCE_COPPER_BOX
        })
        
    return events

if __name__ == "__main__":
    events = fetch_copper_box_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
