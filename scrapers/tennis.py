import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, time
from utils.common import parse_event_date, normalize_price
from params import (
    CATEGORY_SPORTS,
    DAYS_PER_WEEK,
    DISPLAY_DATE_FORMAT,
    HTML_PARSER,
    HTTP_STATUS_OK,
    LABEL_TENNIS,
    PRICE_CHECK_WEBSITE,
    SHORT_DATE_FORMAT,
    SOURCE_TENNIS,
    SUB_PADEL,
    TENNIS_BASE_URL,
    TENNIS_DATE_PLACEHOLDER,
    TENNIS_DESCRIPTION_MAX_CHARS,
    TENNIS_DROPIN_DATE_FORMAT,
    TENNIS_DROPIN_DESCRIPTION,
    TENNIS_DROPIN_HOUR,
    TENNIS_DROPIN_LOCATION,
    TENNIS_DROPIN_MINUTE,
    TENNIS_DROPIN_PRICE,
    TENNIS_DROPIN_SOURCE,
    TENNIS_DROPIN_TITLE,
    TENNIS_DROPIN_URL,
    TENNIS_DROPIN_WEEKDAY,
    TENNIS_TITLE_KEYWORDS,
    TENNIS_URLS,
    USER_AGENT_BROWSER,
)

def fetch_tennis_events():
    events = []
    
    # 1. Lea Valley News/Events
    urls = TENNIS_URLS
    
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }

    for url in urls:
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != HTTP_STATUS_OK: continue
            
            soup = BeautifulSoup(res.text, HTML_PARSER)
            # Look for news items with "Tennis" in title
            # Better.org structure: .view-news-events .views-row
            
            articles = soup.find_all('div', class_='views-row')
            if not articles:
                # Try generic article finding
                articles = soup.find_all('article')
                
            for art in articles:
                title_tag = art.find('h3') or art.find('h2')
                if not title_tag: continue
                title = title_tag.get_text(strip=True)
                
                # Check for Tennis OR Padel
                if not any(k in title.lower() for k in TENNIS_TITLE_KEYWORDS): continue
                
                sub_cat = LABEL_TENNIS
                if SUB_PADEL.lower() in title.lower():
                    sub_cat = SUB_PADEL
                
                # Check for dates
                text = art.get_text()
                # Simple date extraction regex
                date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', text)
                date_obj = None
                date_str = TENNIS_DATE_PLACEHOLDER
                if date_match:
                    try:
                        date_obj = datetime.strptime(date_match.group(1), SHORT_DATE_FORMAT)
                        date_str = date_obj.strftime(DISPLAY_DATE_FORMAT)
                    except: pass
                
                link = art.find('a')
                event_url = url
                if link and link.get('href'):
                    if link.get('href').startswith('http'):
                        event_url = link.get('href')
                    else:
                        event_url = TENNIS_BASE_URL + link.get('href')

                if date_obj and date_obj > datetime.now():
                    events.append({
                        'title': title,
                        'url': event_url,
                        'description': text[:TENNIS_DESCRIPTION_MAX_CHARS].strip() + "...",
                        'date_str': date_str,
                        'date_obj': date_obj,
                        'category': CATEGORY_SPORTS,
                        'sub_category': sub_cat,
                        'price': PRICE_CHECK_WEBSITE,
                        'source': SOURCE_TENNIS
                    })
        except Exception as e:
            print(f"Error scraping tennis url {url}: {e}")

    # Fallback: Static Recurring Event (Women's Drop-in) 
    # ONLY if no dynamic events found, to ensure we have something?
    # Actually, keep it as it's a known reliable event.
    
    today = datetime.now().date()
    days_ahead = TENNIS_DROPIN_WEEKDAY - today.weekday()
    if days_ahead <= 0: days_ahead += DAYS_PER_WEEK
    next_thursday = datetime.now() + timedelta(days=days_ahead)
    next_thursday_dt = datetime.combine(next_thursday.date(), time(TENNIS_DROPIN_HOUR, TENNIS_DROPIN_MINUTE))
    
    events.append({
        'title': TENNIS_DROPIN_TITLE,
        'date_str': next_thursday.strftime(TENNIS_DROPIN_DATE_FORMAT)
                    + f" @ {TENNIS_DROPIN_HOUR:02d}:{TENNIS_DROPIN_MINUTE:02d}",
        'date_obj': next_thursday_dt,
        'location': TENNIS_DROPIN_LOCATION,
        'description': TENNIS_DROPIN_DESCRIPTION,
        'url': TENNIS_DROPIN_URL,
        'category': CATEGORY_SPORTS,
        'sub_category': LABEL_TENNIS,
        'price': TENNIS_DROPIN_PRICE,
        'source': TENNIS_DROPIN_SOURCE
    })

    return events

if __name__ == "__main__":
    events = fetch_tennis_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")

