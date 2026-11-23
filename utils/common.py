from datetime import datetime, date, timedelta
import re
from dateutil import parser

# One home for the report's date window (issue #8).
# Defaults chosen by the implementer; the owner may change them here only.
REPORT_HORIZON_WEEKS = 8     # events dated later than today + this many weeks are dropped
NEWS_MAX_AGE_DAYS = 14       # news/offer items older than this are dropped
NEWS_CATEGORIES = ('News & Alerts', 'Dining & Offers')
DISPLAY_DATE_FORMAT = "%a, %d %b %Y"   # time ' @ HH:MM' is appended when not midnight


def parse_event_date(date_str):
    """
    Parses a date string into a datetime object.
    Returns datetime object or None.
    """
    if not date_str or date_str.lower() in ['see website', 'check website']:
        return None

    try:
        # Try ISO format first
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass

    try:
        # Fuzzy parse using dateutil
        return parser.parse(date_str, fuzzy=True, dayfirst=True)
    except (ValueError, OverflowError):
        return None


def format_event_date(dt):
    """The single display format for every row in the report."""
    text = dt.strftime(DISPLAY_DATE_FORMAT)
    if (dt.hour, dt.minute) != (0, 0):
        text += dt.strftime(" @ %H:%M")
    return text


def _local_date(dt):
    """Calendar date of a datetime; aware values are converted to local time."""
    if dt.tzinfo is not None:
        dt = dt.astimezone()
    return dt.date()


class WindowResult:
    """Outcome of apply_date_window."""

    def __init__(self, kept, dropped_untitled, dropped_past, dropped_later,
                 dropped_stale_news, undated_sources, window):
        self.kept = kept
        self.dropped_untitled = dropped_untitled
        self.dropped_past = dropped_past
        self.dropped_later = dropped_later
        self.dropped_stale_news = dropped_stale_news
        self.undated_sources = undated_sources  # sorted source names, no parseable date
        self.window = window  # (first_date, last_date)

    def check(self):
        """
        Returns ('PASS'|'FAIL'|'INDETERMINATE', details list).
        FAIL: a kept row lies outside the window (self-check of the filter).
        INDETERMINATE: some source gave no parseable date, so the filter could
        not judge its rows; a silent source is not read as 'nothing out of date'.
        """
        first, last = self.window
        bad = []
        for e in self.kept:
            d = _local_date(e['date_obj'])
            lo = first - timedelta(days=NEWS_MAX_AGE_DAYS) if e.get('category') in NEWS_CATEGORIES else first
            if not (lo <= d <= last):
                bad.append(f"{e.get('source')}: {e.get('title')} ({d})")
        if bad:
            return 'FAIL', bad
        if self.undated_sources:
            return 'INDETERMINATE', [f"no parseable date: {s}" for s in self.undated_sources]
        return 'PASS', []

    def summary(self):
        outcome, details = self.check()
        line = (f"Date window {self.window[0]}..{self.window[1]}: {outcome}; "
                f"kept {len(self.kept)}, dropped past {self.dropped_past}, "
                f"later than {REPORT_HORIZON_WEEKS} weeks {self.dropped_later}, "
                f"stale news {self.dropped_stale_news}, untitled {self.dropped_untitled}")
        if details:
            line += "\n  " + "\n  ".join(details)
        return line


def apply_date_window(events, today=None):
    """
    Shared date filter. Drops rows without a title, rows dated before `today`,
    rows dated after today + REPORT_HORIZON_WEEKS, and news older than
    NEWS_MAX_AGE_DAYS. Rewrites date_str of every kept row to one format.
    Rows without a parsed date are dropped and their sources reported.
    """
    today = today or date.today()
    last = today + timedelta(weeks=REPORT_HORIZON_WEEKS)
    kept = []
    untitled = past = later = stale = 0
    undated = set()

    for e in events:
        if not (e.get('title') or '').strip():
            untitled += 1
            continue
        dt = e.get('date_obj')
        if not dt:
            undated.add(e.get('source') or 'unknown')
            continue
        d = _local_date(dt)
        if d > last:
            later += 1
            continue
        if e.get('category') in NEWS_CATEGORIES:
            if (today - d).days > NEWS_MAX_AGE_DAYS:
                stale += 1
                continue
        elif d < today:
            past += 1
            continue
        e['date_str'] = format_event_date(dt)
        kept.append(e)

    return WindowResult(kept, untitled, past, later, stale, sorted(undated), (today, last))


def normalize_price(price_text):
    """
    Extracts the price range.
    """
    if not price_text:
        return "Check website"

    price_text = price_text.lower()
    if 'free' in price_text:
        return "Free"

    # Find numbers with £
    prices = re.findall(r'£(\d+(?:\.\d{2})?)', price_text)
    if prices:
        vals = sorted([float(p) for p in prices])
        if not vals: return "Check website"
        if len(vals) == 1:
            return f"£{vals[0]:.2f}"
        return f"£{vals[0]:.2f} - £{vals[-1]:.2f}"

    return "Check website"
