import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.common import parse_event_date, normalize_price
import re
from params import (
    CATEGORY_EAST_VILLAGE,
    CATEGORY_QEOP_GENERAL,
    CATEGORY_RIVERSIDE_EAST,
    DATE_SEE_WEBSITE,
    DESCRIPTION_MAX_CHARS,
    HTML_PARSER,
    KEYWORD_MARKET,
    QEOP_BASE_URL,
    QEOP_DEFAULT_SUBCATEGORY,
    QEOP_EAST_VILLAGE_KEYWORD,
    QEOP_EVENTS_URL,
    QEOP_MIN_DESCRIPTION_CHARS,
    QEOP_PRICE_DEFAULT,
    QEOP_RIVERSIDE_KEYWORD,
    QEOP_TOUR_KEYWORDS,
    SOURCE_QEOP,
    SUB_QEOP_MARKETS,
    SUB_QEOP_RIVERSIDE,
    SUB_QEOP_TOURS,
    USER_AGENT_BROWSER,
)

def fetch_qeop_events():
    url = QEOP_EVENTS_URL
    headers = {
        "User-Agent": USER_AGENT_BROWSER
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching QEOP events: {e}")
        return []

    soup = BeautifulSoup(response.text, HTML_PARSER)
    events = []

    articles = soup.find_all('article', class_=re.compile(r'o-teaser'))

    for article in articles:
        title_tag = article.find('h3', class_='o-teaser__title')
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        link_tag = title_tag.find('a')
        if link_tag and link_tag.get('href'):
            event_url = QEOP_BASE_URL + link_tag.get('href')
        else:
            event_url = url

        # Shallow scrape fallback
        summary_tag = article.find('div', class_='o-teaser__summary')
        description = summary_tag.get_text(strip=True) if summary_tag else ""

        date_tag = article.find('div', class_='o-teaser__date') or article.find('time')
        date_raw = date_tag.get_text(strip=True) if date_tag else DATE_SEE_WEBSITE
        
        # Deep scrape for full text / date check
        price_str = QEOP_PRICE_DEFAULT
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, HTML_PARSER)
            
            # Content
            # Usually in .o-wysiwyg or similar
            content_div = soup_d.find('div', class_=re.compile(r'wysiwyg'))
            if content_div:
                full_text = content_div.get_text(strip=True)
                if len(full_text) > QEOP_MIN_DESCRIPTION_CHARS: description = full_text[:DESCRIPTION_MAX_CHARS] + "..."
            
            # Check price keywords
            body_text = soup_d.get_text().lower()
            if '£' in body_text:
                price_str = normalize_price(soup_d.get_text())
                
        except:
            pass

        date_obj = parse_event_date(date_raw)
        
        sub_cat = QEOP_DEFAULT_SUBCATEGORY
        t_low = title.lower()
        if any(k in t_low for k in QEOP_TOUR_KEYWORDS): sub_cat = SUB_QEOP_TOURS
        elif KEYWORD_MARKET in t_low: sub_cat = SUB_QEOP_MARKETS
        
        cat = CATEGORY_QEOP_GENERAL
        if QEOP_RIVERSIDE_KEYWORD in t_low or QEOP_RIVERSIDE_KEYWORD in description.lower():
            cat = CATEGORY_RIVERSIDE_EAST
            sub_cat = SUB_QEOP_RIVERSIDE
        elif QEOP_EAST_VILLAGE_KEYWORD in t_low:
            cat = CATEGORY_EAST_VILLAGE

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': cat,
            'sub_category': sub_cat,
            'price': price_str,
            'source': SOURCE_QEOP
        })

    return events

if __name__ == "__main__":
    events = fetch_qeop_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
