import requests
from bs4 import BeautifulSoup
from datetime import datetime
from utils.common import parse_event_date, normalize_price
import re

def fetch_qeop_events():
    url = "https://www.queenelizabetholympicpark.co.uk/whats-on"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching QEOP events: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []

    articles = soup.find_all('article', class_=re.compile(r'o-teaser'))

    for article in articles:
        title_tag = article.find('h3', class_='o-teaser__title')
        if not title_tag: continue
        title = title_tag.get_text(strip=True)
        
        link_tag = title_tag.find('a')
        if link_tag and link_tag.get('href'):
            event_url = "https://www.queenelizabetholympicpark.co.uk" + link_tag.get('href')
        else:
            event_url = url

        # Shallow scrape fallback
        summary_tag = article.find('div', class_='o-teaser__summary')
        description = summary_tag.get_text(strip=True) if summary_tag else ""

        date_tag = article.find('div', class_='o-teaser__date') or article.find('time')
        date_raw = date_tag.get_text(strip=True) if date_tag else "See website"
        
        # Deep scrape for full text / date check
        price_str = "Free (check details)"
        try:
            res_d = requests.get(event_url, headers=headers)
            soup_d = BeautifulSoup(res_d.text, 'html.parser')
            
            # Content
            # Usually in .o-wysiwyg or similar
            content_div = soup_d.find('div', class_=re.compile(r'wysiwyg'))
            if content_div:
                full_text = content_div.get_text(strip=True)
                if len(full_text) > 20: description = full_text[:300] + "..."
            
            # Check price keywords
            body_text = soup_d.get_text().lower()
            if '£' in body_text:
                price_str = normalize_price(soup_d.get_text())
                
        except:
            pass

        date_obj = parse_event_date(date_raw)
        
        sub_cat = 'General Park Event'
        t_low = title.lower()
        if 'tour' in t_low or 'trail' in t_low: sub_cat = 'Tours & Trails'
        elif 'market' in t_low: sub_cat = 'Markets'
        
        cat = 'QEOP / General'
        if 'riverside east' in t_low or 'riverside east' in description.lower():
            cat = 'Riverside East'
            sub_cat = 'Events'
        elif 'east village' in t_low:
            cat = 'East Village'

        events.append({
            'title': title,
            'url': event_url,
            'description': description,
            'date_str': date_raw,
            'date_obj': date_obj,
            'category': cat,
            'sub_category': sub_cat,
            'price': price_str,
            'source': 'Queen Elizabeth Olympic Park'
        })

    return events

if __name__ == "__main__":
    events = fetch_qeop_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
