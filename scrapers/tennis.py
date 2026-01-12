import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, time
from utils.common import parse_event_date, normalize_price

def fetch_tennis_events():
    events = []
    
    # 1. Lea Valley News/Events
    urls = [
        "https://www.better.org.uk/leisure-centre/lee-valley/hockey-and-tennis-centre/news",
        "https://www.leevalleypark.org.uk/press-releases/lee-valley-hockey-and-tennis-centre-update"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for url in urls:
        try:
            res = requests.get(url, headers=headers)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.text, 'html.parser')
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
                if 'tennis' not in title.lower() and 'padel' not in title.lower(): continue
                
                sub_cat = 'Tennis'
                if 'padel' in title.lower():
                    sub_cat = 'Padel'
                
                # Check for dates
                text = art.get_text()
                # Simple date extraction regex
                date_match = re.search(r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})', text)
                date_obj = None
                date_str = "See link"
                if date_match:
                    try:
                        date_obj = datetime.strptime(date_match.group(1), "%d %b %Y")
                        date_str = date_obj.strftime("%a, %d %b %Y")
                    except: pass
                
                link = art.find('a')
                event_url = url
                if link and link.get('href'):
                    if link.get('href').startswith('http'):
                        event_url = link.get('href')
                    else:
                        event_url = "https://www.better.org.uk" + link.get('href')

                if date_obj and date_obj > datetime.now():
                    events.append({
                        'title': title,
                        'url': event_url,
                        'description': text[:200].strip() + "...",
                        'date_str': date_str,
                        'date_obj': date_obj,
                        'category': 'Sports',
                        'sub_category': sub_cat,
                        'price': "Check website",
                        'source': 'Lea Valley Tennis'
                    })
        except Exception as e:
            print(f"Error scraping tennis url {url}: {e}")

    # Fallback: Static Recurring Event (Women's Drop-in) 
    # ONLY if no dynamic events found, to ensure we have something?
    # Actually, keep it as it's a known reliable event.
    
    today = datetime.now().date()
    days_ahead = 3 - today.weekday()
    if days_ahead <= 0: days_ahead += 7
    next_thursday = datetime.now() + timedelta(days=days_ahead)
    next_thursday_dt = datetime.combine(next_thursday.date(), time(10, 0))
    
    events.append({
        'title': "Women's Tennis Drop-In",
        'date_str': next_thursday.strftime("%A, %d %B %Y") + " @ 10:00",
        'date_obj': next_thursday_dt,
        'location': "Lea Valley Hockey and Tennis Centre",
        'description': "Weekly drop-in session. Check website for cancellations.",
        'url': "https://www.better.org.uk/leisure-centre/london/queen-elizabeth-olympic-park/lee-valley-hockey-and-tennis-centre/timetable",
        'category': 'Sports',
        'sub_category': 'Tennis',
        'price': "£8.00 - £10.00",
        'source': 'Better / Lea Valley'
    })

    return events

if __name__ == "__main__":
    events = fetch_tennis_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")

