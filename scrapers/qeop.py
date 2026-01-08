import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

def fetch_qeop_events():
    url = "https://www.queenelizabetholympicpark.co.uk/whats-on"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch QEOP events: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    events = []

    # Find all event articles
    articles = soup.find_all('article', class_=re.compile(r'o-teaser'))

    for article in articles:
        event = {}
        
        # Title
        title_tag = article.find('h3', class_='o-teaser__title')
        if not title_tag:
            continue
        event['title'] = title_tag.get_text(strip=True)
        
        # Link
        link_tag = title_tag.find('a')
        if link_tag and link_tag.get('href'):
            event['url'] = "https://www.queenelizabetholympicpark.co.uk" + link_tag.get('href')
        else:
            event['url'] = url

        # Description / Info (often in o-teaser__summary or similar)
        summary_tag = article.find('div', class_='o-teaser__summary')
        event['description'] = summary_tag.get_text(strip=True) if summary_tag else ""

        # Date - usually in a specific field or metadata
        # Let's look for dates in the teaser
        date_tag = article.find('div', class_='o-teaser__date') or article.find('time')
        event['date_str'] = date_tag.get_text(strip=True) if date_tag else "Check website"

        # Categories
        cat_tag = article.find('div', class_='o-teaser__category')
        event['category'] = cat_tag.get_text(strip=True) if cat_tag else ""

        events.append(event)

    return events

if __name__ == "__main__":
    events = fetch_qeop_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")
