"""TfL Tube Strike Alerts — first item in weekly report.

Sources (in order of preference):
1. TfL Unified API: /Line/Mode/tube/Disruption (structured, reliable)
2. Fallback: scrape https://tfl.gov.uk/campaign/strikes (HTML)

Returns events with category='⚠️ Tube Strikes' to appear first in report.
"""
import requests
from datetime import datetime, timedelta
from params import (
    CATEGORY_TUBE_STRIKES,
    HTML_PARSER,
    HTTP_STATUS_OK,
    HTTP_TIMEOUT_SECONDS,
    PRICE_NONE,
    SHORT_DATE_FORMAT,
    SOURCE_TFL,
    SUB_TFL_INDUSTRIAL_ACTION,
    SUB_TFL_STATUS,
    TFL_API_STRIKE_KEYWORDS,
    TFL_API_TITLE_TEMPLATE,
    TFL_DATE_TBC,
    TFL_DEFAULT_DESCRIPTION,
    TFL_DEFAULT_LINES,
    TFL_DESCRIPTION_MAX_CHARS,
    TFL_DISRUPTION_URL,
    TFL_HEADING_DATE_PATTERNS,
    TFL_LOOKAHEAD_DAYS,
    TFL_NO_STRIKES_DATE_TEMPLATE,
    TFL_NO_STRIKES_DESCRIPTION,
    TFL_NO_STRIKES_TITLE,
    TFL_NO_YEAR_PLACEHOLDER,
    TFL_PAGE_DEFAULT_DESCRIPTION,
    TFL_PAGE_STRIKE_KEYWORDS,
    TFL_PAGE_TITLE_TEMPLATE,
    TFL_RANGE_DATE_FORMAT,
    TFL_STRIKES_URL,
    TFL_USER_AGENT,
)

HEADERS = {"User-Agent": TFL_USER_AGENT}


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
            'title': TFL_NO_STRIKES_TITLE,
            'url': TFL_STRIKES_URL,
            'description': TFL_NO_STRIKES_DESCRIPTION,
            'date_str': TFL_NO_STRIKES_DATE_TEMPLATE.format(date=datetime.now().strftime(SHORT_DATE_FORMAT)),
            'date_obj': datetime.now(),
            'category': CATEGORY_TUBE_STRIKES,
            'sub_category': SUB_TFL_STATUS,
            'price': PRICE_NONE,
            'source': SOURCE_TFL
        }]

    return events


def _fetch_via_api():
    """Use TfL Unified API to find planned disruptions (strikes)."""
    events = []
    now = datetime.now()
    week_ahead = now + timedelta(days=TFL_LOOKAHEAD_DAYS)

    # Check for planned closures/disruptions on tube lines
    # The /Line/Mode/tube/Disruption endpoint shows current + future disruptions
    url = TFL_DISRUPTION_URL
    resp = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT_SECONDS)

    if resp.status_code != HTTP_STATUS_OK:
        raise RuntimeError(f"TfL API returned {resp.status_code}")

    disruptions = resp.json()

    for d in disruptions:
        # Filter to strikes/industrial action only
        desc = (d.get('description', '') + ' ' + d.get('additionalInfo', '')).lower()
        category_desc = d.get('categoryDescription', '').lower()

        is_strike = any(kw in desc or kw in category_desc for kw in TFL_API_STRIKE_KEYWORDS)

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
        lines_str = ', '.join(lines) if lines else TFL_DEFAULT_LINES

        date_str = from_date.strftime(TFL_RANGE_DATE_FORMAT) if from_date else TFL_DATE_TBC
        if to_date and to_date != from_date:
            date_str += f" – {to_date.strftime(TFL_RANGE_DATE_FORMAT)}"

        events.append({
            'title': TFL_API_TITLE_TEMPLATE.format(lines=lines_str),
            'url': TFL_STRIKES_URL,
            'description': d.get('description', TFL_DEFAULT_DESCRIPTION),
            'date_str': date_str,
            'date_obj': from_date or now,
            'category': CATEGORY_TUBE_STRIKES,
            'sub_category': SUB_TFL_INDUSTRIAL_ACTION,
            'price': PRICE_NONE,
            'source': SOURCE_TFL
        })

    return events


def _fetch_via_scrape():
    """Fallback: scrape tfl.gov.uk/campaign/strikes page."""
    from bs4 import BeautifulSoup

    events = []
    resp = requests.get(TFL_STRIKES_URL, headers=HEADERS, timeout=HTTP_TIMEOUT_SECONDS)

    if resp.status_code != HTTP_STATUS_OK:
        raise RuntimeError(f"TfL strikes page returned {resp.status_code}")

    soup = BeautifulSoup(resp.text, HTML_PARSER)

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
        if any(kw in combined for kw in TFL_PAGE_STRIKE_KEYWORDS):
            events.append({
                'title': TFL_PAGE_TITLE_TEMPLATE.format(text=text),
                'url': TFL_STRIKES_URL,
                'description': desc[:TFL_DESCRIPTION_MAX_CHARS] if desc else TFL_PAGE_DEFAULT_DESCRIPTION,
                'date_str': text,
                'date_obj': date_obj or datetime.now(),
                'category': CATEGORY_TUBE_STRIKES,
                'sub_category': SUB_TFL_INDUSTRIAL_ACTION,
                'price': PRICE_NONE,
                'source': SOURCE_TFL
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
    patterns = TFL_HEADING_DATE_PATTERNS
    for fmt, regex in patterns:
        match = re.search(regex, text)
        if match:
            try:
                d = datetime.strptime(match.group(), fmt)
                if d.year == TFL_NO_YEAR_PLACEHOLDER:  # no year in format
                    d = d.replace(year=datetime.now().year)
                return d
            except ValueError:
                continue
    return None
