from datetime import datetime
import re
from dateutil import parser

def parse_event_date(date_str):
    """
    Parses a date string into a datetime object.
    Returns datetime object or None.
    """
    if not date_str or date_str.lower() in ['see website', 'check website']:
        return None
        
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_raw)
    except:
        pass
        
    try:
        # Fuzzy parse using dateutil
        dt = parser.parse(date_str, fuzzy=True, dayfirst=True)
        return dt
    except:
        return None

def normalize_price(price_text):
    """
    Extracts the minimum adult price.
    """
    if not price_text:
        return "Check website"
    
    price_text = price_text.lower()
    if 'free' in price_text:
        return "Free"
        
    # Find numbers with £
    prices = re.findall(r'£\d+(?:\.\d{2})?', price_text)
    if prices:
        # distinct prices, sorted
        vals = sorted([float(p.replace('£','')) for p in prices])
        return f"£{vals[0]:.2f}"
        
    return "Check website"
