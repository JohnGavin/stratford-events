"""TfL Tube Strike Alerts — first item in weekly report.

Sources (in order of preference):
1. TfL Unified API: /Line/Mode/tube/Disruption (structured, reliable)
2. Fallback: scrape https://tfl.gov.uk/campaign/strikes (HTML)

Returns events with category='⚠️ Tube Strikes' to appear first in report.
"""
import requests
from datetime import datetime, timedelta

TFL_API_BASE = "https://api.tfl.gov.uk"
TFL_STRIKES_URL = "https://tfl.gov.uk/campaign/strikes"
HEADERS = {
    "User-Agent": "StratfordEventsBot/1.0 (weekly personal report)"
}


def fetch_tfl_strikes():
    """Fetch upcoming tube strikes for the next 7 days."""
    events = []

    # Try TfL Unified API first (no key needed for basic access)
    try:
        events = _fetch_via_api()
    except Exception as e:
        print(f"TfL API failed ({e}), trying scrape fallback...")

    # Fallback: scrape the strikes page
    if not events:
        try:
            events = _fetch_via_scrape()
        except Exception as e:
            print(f"TfL scrape also failed: {e}")

    # If no strikes found, return a "no strikes" placeholder
    if not events:
        events = [{
            'title': 'No tube strikes planned',
            'url': TFL_STRIKES_URL,
            'description': 'No industrial action affecting London Underground is currently planned for the coming week.',
            'date_str': f"Week of {datetime.now().strftime('%d %b %Y')}",
            'date_obj': datetime.now(),
            'category': '⚠️ Tube Strikes',
            'sub_category': 'Status',
            'price': '-',
            'source': 'TfL'
        }]

    return events


def _fetch_via_api():
    """Use TfL Unified API to find planned disruptions (strikes)."""
    events = []
    now = datetime.now()
    week_ahead = now + timedelta(days=7)

    # Check for planned closures/disruptions on tube lines
    # The /Line/Mode/tube/Disruption endpoint shows current + future disruptions
    url = f"{TFL_API_BASE}/Line/Mode/tube/Disruption"
    resp = requests.get(url, headers=HEADERS, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"TfL API returned {resp.status_code}")

    disruptions = resp.json()

    for d in disruptions:
        # Filter to strikes/industrial action only
        desc = (d.get('description', '') + ' ' + d.get('additionalInfo', '')).lower()
        category_desc = d.get('categoryDescription', '').lower()

        is_strike = any(kw in desc or kw in category_desc for kw in [
            'strike', 'industrial action', 'walkout', 'rmt', 'aslef', 'tssa'
        ])

        if not is_strike:
            continue

        # Parse dates
        from_date = _parse_tfl_date(d.get('fromDate'))
        to_date = _parse_tfl_date(d.get('toDate'))

        # Only include if within next 7 days
        if from_date and from_date > week_ahead:
            continue
        if to_date and to_date < now:
            continue

        # Affected lines
        affected = d.get('affectedRoutes', [])
        lines = [r.get('name', '') for r in affected] if affected else []
        lines_str = ', '.join(lines) if lines else 'Multiple lines'

        date_str = from_date.strftime('%a %d %b') if from_date else 'TBC'
        if to_date and to_date != from_date:
            date_str += f" – {to_date.strftime('%a %d %b')}"

        events.append({
            'title': f"🚇 Tube Strike: {lines_str}",
            'url': TFL_STRIKES_URL,
            'description': d.get('description', 'Industrial action planned.'),
            'date_str': date_str,
            'date_obj': from_date or now,
            'category': '⚠️ Tube Strikes',
            'sub_category': 'Industrial Action',
            'price': '-',
            'source': 'TfL'
        })

    return events


def _fetch_via_scrape():
    """Fallback: scrape tfl.gov.uk/campaign/strikes page."""
    from bs4 import BeautifulSoup

    events = []
    resp = requests.get(TFL_STRIKES_URL, headers=HEADERS, timeout=15)

    if resp.status_code != 200:
        raise RuntimeError(f"TfL strikes page returned {resp.status_code}")

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Look for strike content blocks
    # The page structure varies but typically has date/description blocks
    content = soup.find('div', class_='content-area') or soup.find('main')
    if not content:
        return events

    # Look for headings or paragraphs mentioning strikes
    for heading in content.find_all(['h2', 'h3', 'strong']):
        text = heading.get_text(strip=True)
        if not text:
            continue

        # Try to extract date from heading
        date_obj = _try_parse_date(text)

        # Get description from next sibling
        desc = ''
        next_el = heading.find_next_sibling(['p', 'ul', 'div'])
        if next_el:
            desc = next_el.get_text(strip=True)

        # Only include if it looks like strike info
        combined = (text + ' ' + desc).lower()
        if any(kw in combined for kw in ['strike', 'industrial action', 'walkout', 'disruption']):
            events.append({
                'title': f"🚇 {text}",
                'url': TFL_STRIKES_URL,
                'description': desc[:300] if desc else 'See TfL website for details.',
                'date_str': text,
                'date_obj': date_obj or datetime.now(),
                'category': '⚠️ Tube Strikes',
                'sub_category': 'Industrial Action',
                'price': '-',
                'source': 'TfL'
            })

    return events


def _parse_tfl_date(date_str):
    """Parse TfL API date format (ISO 8601)."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00')).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def _try_parse_date(text):
    """Try common date formats in heading text."""
    import re
    # Try "DD Month YYYY" or "DD Month"
    patterns = [
        ("%d %B %Y", r'\d{1,2} \w+ \d{4}'),
        ("%d %B", r'\d{1,2} \w+'),
        ("%A %d %B", r'\w+ \d{1,2} \w+'),
    ]
    for fmt, regex in patterns:
        match = re.search(regex, text)
        if match:
            try:
                d = datetime.strptime(match.group(), fmt)
                if d.year == 1900:  # no year in format
                    d = d.replace(year=datetime.now().year)
                return d
            except ValueError:
                continue
    return None
