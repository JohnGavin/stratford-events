"""Single home for every tunable constant and parameter of the weekly report.

Rule (owner, 2026-11-23): move all constants / parameters to ONE source of truth
for the project; do not leave them scattered in multiple files.

* Change a value here and nowhere else. Every other module imports from here.
* A value that is derived from another is derived below, never retyped.
* tests/test_params_single_home.py fails the build if a value defined here
  reappears as a literal in any other .py file, or if a name is defined twice.
* Secrets and recipient addresses are NOT parameters: they live in environment
  variables / GitHub secrets. Only the NAMES of those variables are kept here.
* Left out on purpose (parser internals, not tunables): CSS selectors and regexes
  that describe a page's HTML structure, and the CSS in report_template.html.

Sections: 1 labels, 2 report window, 3 formats, 4 report layout and global
filters, 5 HTTP and shared scraper limits, 6 scrapers (one block per source),
7 email, 8 CI.
"""

# ---------------------------------------------------------------------------
# 1. Labels: categories, sub-categories, sources, price and date placeholders
# ---------------------------------------------------------------------------
CATEGORY_TUBE_STRIKES = '⚠️ Tube Strikes'
CATEGORY_DINING = 'Dining & Offers'
CATEGORY_FREE_CONCERTS = 'Lunchtime Concerts / Free Events'
CATEGORY_STEM = 'STEM / Factual'
CATEGORY_THEATRE = 'Theatre'
LABEL_TENNIS = 'Tennis'          # used as a category name and as a sub-category name
CATEGORY_RIVERSIDE_EAST = 'Riverside East'
CATEGORY_EAST_VILLAGE = 'East Village'
CATEGORY_SHOPPING = 'Westfield / Shopping'
CATEGORY_COMMUNITY = 'Community'
CATEGORY_NEWS = 'News & Alerts'
CATEGORY_OTHER = 'Other'
CATEGORY_SPORTS = 'Sports'
CATEGORY_QEOP_GENERAL = 'QEOP / General'

SUB_GENERAL = 'General'
SUB_PADEL = 'Padel'
SUB_BASKETBALL = 'Basketball'
SUB_BOXING = 'Boxing'
SUB_NETBALL = 'Netball'
SUB_GENERAL_SPORT = 'General Sport'
SUB_MUSEUM = 'Museum / Exhibition'

SOURCE_GOOGLE_NEWS = 'Google News'
SOURCE_BARBICAN = 'Barbican'
SOURCE_GSMD = 'Guildhall School'
SOURCE_GREAT_ST_BARTS = 'Great St Barts'
SOURCE_ST_STEPHEN = 'St Stephen Walbrook'
SOURCE_HERE_EAST = 'Here East'
SOURCE_LSO = 'LSO'
SOURCE_STRATFORD_EAST = 'Stratford East'
SOURCE_VA = 'V&A East'
SOURCE_BARTS = 'Barts North Wing'
SUB_SADLERS = "Sadler's Wells"

PRICE_FREE = 'Free'
PRICE_CHECK_WEBSITE = 'Check website'
PRICE_NONE = '-'
DATE_SEE_WEBSITE = 'See website'

# ---------------------------------------------------------------------------
# 2. Report window (issue #8)
# ---------------------------------------------------------------------------
REPORT_HORIZON_WEEKS = 8      # events dated later than today + this many weeks are dropped
NEWS_MAX_AGE_DAYS = 14        # news/offer items older than this are dropped
NEWS_CATEGORIES = (CATEGORY_NEWS, CATEGORY_DINING)
DAYS_PER_WEEK = 7             # calendar fact, used for weekday arithmetic
MONTHS_PER_YEAR = 12          # calendar fact, used for next-month arithmetic
HTTP_STATUS_OK = 200          # protocol fact: a fetch counts as successful on this status

# ---------------------------------------------------------------------------
# 3. Date and time formats
# ---------------------------------------------------------------------------
DISPLAY_DATE_FORMAT = "%a, %d %b %Y"            # the single display format in the report
DISPLAY_TIME_SUFFIX_FORMAT = " @ %H:%M"         # appended when the time is not midnight
ISO_DATE_FORMAT = "%Y-%m-%d"
SHORT_DATE_FORMAT = "%d %b %Y"                  # tennis page dates, email subject, TfL placeholder
LONG_DATE_FORMAT = "%A %d %B %Y"
TIME_12H_FORMAT = "%I:%M%p"
TIME_24H_FORMAT = "%H:%M"
LONG_DATETIME_12H_FORMAT = LONG_DATE_FORMAT + ", " + TIME_12H_FORMAT
NEWS_PUBDATE_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"   # RFC 822 pubDate of the Google News RSS
REPORT_TODAY_FORMAT = "%d %B %Y"                # "Generated on ..." in the report footer

# ---------------------------------------------------------------------------
# 4. Report layout and global filters (main.py)
# ---------------------------------------------------------------------------
REPORT_TITLE = "Stratford Events Weekly Report"
REPORT_TAGLINE = "Your curated guide to upcoming STEM, Sports, and Culture in Stratford (E15/E20)."
REPORT_TEMPLATE_FILE = 'report_template.html'
REPORT_OUTPUT_FILE = 'report.html'

# Order of the category sections in the report; categories not listed are not shown.
CATEGORY_ORDER = [
    CATEGORY_TUBE_STRIKES, CATEGORY_DINING, CATEGORY_FREE_CONCERTS, CATEGORY_STEM,
    CATEGORY_THEATRE, LABEL_TENNIS, CATEGORY_RIVERSIDE_EAST, CATEGORY_EAST_VILLAGE,
    CATEGORY_SHOPPING, CATEGORY_COMMUNITY, CATEGORY_NEWS, CATEGORY_OTHER, CATEGORY_SPORTS,
]

# Any event whose title or description contains one of these words is dropped.
GLOBAL_FORBIDDEN_KEYWORDS = [
    'football', 'musical', 'dance', 'pantomime', 'panto', 'ballet', 'opera',
    'women', 'woman', 'ladies', 'kid', 'child', 'junior', 'boy', 'girl', 'family',
    'netball', 'road close',
]
# Free events from these sources are moved to the free-concerts category.
FREE_RECATEGORIZE_SOURCES = [SOURCE_BARBICAN, SOURCE_GSMD, SOURCE_GREAT_ST_BARTS, SOURCE_ST_STEPHEN]

SPORTS_SINGLE_ITEM_SUBCATEGORIES = [SUB_BASKETBALL, SUB_BOXING]   # show only the next event
SPORTS_SINGLE_ITEM_LIMIT = 1
SPORTS_SUBCATEGORY_PRIORITY = [LABEL_TENNIS, SUB_PADEL]           # listed first in Sports
GOOGLE_NEWS_ITEMS_PER_SUBCATEGORY = 1
UNDATED_SORT_TIMESTAMP = 9999999999.0        # undated events sort last

# Display name of each scraper in the run log; also the default 'source' of its rows.
SCRAPER_LABELS = {
    'tfl_strikes': 'TfL Strikes',     # FIRST: appears at top of report
    'qeop': 'QEOP',
    'ucl': 'UCL',
    'sports': CATEGORY_SPORTS,
    'theatre': CATEGORY_THEATRE,
    'here_east': SOURCE_HERE_EAST,
    'lea_valley': LABEL_TENNIS,
    'va_east': SOURCE_VA,
    'sadlers': SUB_SADLERS,
    'gsmd': SOURCE_GSMD,
    'news': 'News',
    'dining': CATEGORY_DINING,
    'aquatics': 'Aquatics',
    'barbican': SOURCE_BARBICAN,
    'lso': SOURCE_LSO,
    'barts_north_wing': SOURCE_BARTS,
    'st_brides': 'St Brides',
    'great_st_barts': SOURCE_GREAT_ST_BARTS,
    'st_stephen': SOURCE_ST_STEPHEN,
}

# ---------------------------------------------------------------------------
# 5. HTTP and shared scraper limits
# ---------------------------------------------------------------------------
USER_AGENT_BROWSER = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/91.0.4472.124 Safari/537.36"
)
HTTP_TIMEOUT_SECONDS = 15
HTML_PARSER = 'html.parser'          # BeautifulSoup parser backend used by every HTML scraper
DESCRIPTION_MAX_CHARS = 300          # event descriptions are cut to this length
GOOGLE_NEWS_RSS_URL_TEMPLATE = "https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
NEWS_ITEMS_PER_QUERY = 3             # top hits kept per Google News query

# ---------------------------------------------------------------------------
# 6. Scrapers, one block per source
# ---------------------------------------------------------------------------
# --- Google Alerts (scrapers/alerts.py)
ALERTS_QUERIES = [
    "Stratford London events",
    "Queen Elizabeth Olympic Park news",
    "UCL East events",
    "East Bank Stratford",
]
ALERTS_MAX_AGE_DAYS = 30
SUB_GOOGLE_ALERTS = 'Google Alerts'

# --- Dining news (scrapers/dining.py)
DINING_QUERIES = [
    "Stratford London new restaurant",
    "Westfield Stratford City dining news",
    "Stratford E20 restaurant opening",
    "Stratford London food offers",
    "Westfield Stratford new opening",
]
DINING_MAX_AGE_DAYS = 60             # openings stay relevant longer than other news
DINING_HTTP_TIMEOUT_SECONDS = 10
DINING_STRATFORD_KEYWORDS = [
    'stratford', 'westfield', 'e20', 'e15',
    'olympic park', 'queen elizabeth',
    'here east', 'east village', 'east bank',
]
DINING_GENERIC_KEYWORDS = [
    'best restaurants in london',
    'hot new openings',
    'mapped:',
    'london restaurants',
    'openings coming soon',
    'check your area',
    'top restaurants',
    'restaurant guide',
    'where to eat in london',
    'best places to eat',
]
SUB_DINING_NEWS = 'News & Openings'

# --- London Aquatics Centre (scrapers/aquatics.py)
AQUATICS_EVENTS_URL = "https://www.londonaquaticscentre.org/events/"
AQUATICS_DISRUPTION_KEYWORDS = ['disruption', 'closure', 'update', 'info', 'notice']
SUB_AQUATICS = 'Swimming / Aquatics'
SOURCE_AQUATICS = 'London Aquatics Centre'

# --- Barbican (scrapers/barbican.py)
BARBICAN_BASE_URL = "https://www.barbican.org.uk"
BARBICAN_EVENTS_URL = BARBICAN_BASE_URL + "/whats-on"
BARBICAN_MAX_LOOKAHEAD_DAYS = 14
SUB_BARBICAN = 'Barbican Centre'

# --- Barts North Wing (scrapers/barts_north_wing.py)
BARTS_EVENTS_URL = "https://bartsnorthwing.org.uk/whats-on/"
BARTS_DESCRIPTION = "Barts North Wing Event"

# --- Great St Barts (scrapers/great_st_barts.py)
GREAT_ST_BARTS_API_URL_TEMPLATE = (
    "https://greatstbarts.churchsuite.com/embed/calendar/json?date_start={start}&date_end={end}"
)
GREAT_ST_BARTS_FALLBACK_URL = "https://www.greatstbarts.com/events"
GREAT_ST_BARTS_EVENT_URL_TEMPLATE = "https://greatstbarts.churchsuite.com/events/{identifier}"
GREAT_ST_BARTS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
GREAT_ST_BARTS_EXCLUDE_PATTERN = r'evensong|reading|eucharist|communion|prayer|mass|vespers|compline|matins'
GREAT_ST_BARTS_MUSIC_PATTERN = r'concert|recital|music|organ|choir|singing|jazz|ensemble|quartet|trio|sonata|symphony'
GREAT_ST_BARTS_LOCATION = "Great St Bartholomew's Church"
GREAT_ST_BARTS_DESCRIPTION = "Free musical event at Great St Barts"

# --- Guildhall School of Music & Drama (scrapers/gsmd.py)
GSMD_BASE_URL = "https://www.gsmd.ac.uk"
GSMD_EVENTS_URL = GSMD_BASE_URL + "/whats-on"
GSMD_EAST_KEYWORDS = ['Stratford', 'East Bank', 'Olympic Park']   # only events mentioning these
GSMD_MAX_LOOKAHEAD_DAYS = 14
SUB_GSMD = 'GSMD East'

# --- Here East (scrapers/here_east.py)
HERE_EAST_BASE_URL = "https://hereeast.com"
HERE_EAST_EVENTS_URL = HERE_EAST_BASE_URL + "/events/"
HERE_EAST_MIN_DESCRIPTION_CHARS = 30       # first paragraph longer than this becomes the description
HERE_EAST_ERROR_DESCRIPTION = "Click link for details."
HERE_EAST_DEFAULT_SUBCATEGORY = 'Tech/Innovation'
KEYWORD_MARKET = 'market'
HERE_EAST_SUBCATEGORY_KEYWORDS = ((KEYWORD_MARKET, 'Market'), ('cinema', 'Cinema'))

# --- London Symphony Orchestra (scrapers/lso.py)
LSO_BASE_URL = "https://www.lso.co.uk"
LSO_EVENTS_URL = LSO_BASE_URL + "/whats-on/?category=free-friday-lunchtime-concerts"
LSO_CATEGORY_MAX_CHARS = 30                 # a shorter first paragraph is read as the category line
LSO_DESCRIPTION = "Free Friday Lunchtime Concert at LSO St Luke's"
LSO_LOCATION = "LSO St Luke's"

# --- Queen Elizabeth Olympic Park (scrapers/qeop.py)
QEOP_BASE_URL = "https://www.queenelizabetholympicpark.co.uk"
QEOP_EVENTS_URL = QEOP_BASE_URL + "/whats-on"
QEOP_MIN_DESCRIPTION_CHARS = 20
QEOP_PRICE_DEFAULT = "Free (check details)"
QEOP_DEFAULT_SUBCATEGORY = 'General Park Event'
QEOP_TOUR_KEYWORDS = ('tour', 'trail')
SUB_QEOP_TOURS = 'Tours & Trails'
SUB_QEOP_MARKETS = 'Markets'
SUB_QEOP_RIVERSIDE = 'Events'
QEOP_RIVERSIDE_KEYWORD = CATEGORY_RIVERSIDE_EAST.lower()
QEOP_EAST_VILLAGE_KEYWORD = CATEGORY_EAST_VILLAGE.lower()
SOURCE_QEOP = 'Queen Elizabeth Olympic Park'

# --- Sadler's Wells East (scrapers/sadlers.py)
SADLERS_BASE_URL = "https://www.sadlerswells.com"
SADLERS_EVENTS_URL = SADLERS_BASE_URL + "/whats-on/?location=sadlers-wells-east"
SOURCE_SADLERS = "Sadler's Wells East"
SADLERS_VENUE_TEXTS = [SOURCE_SADLERS, "The Dance Floor"]   # a card must mention one
KEYWORD_FREE = 'free'                          # also used when reading prices (utils/common.py)
SADLERS_TITLE_KEYWORDS = ['workshop', 'talk', 'social', KEYWORD_FREE, 'class', 'community', 'floor']
SADLERS_PERFORMANCE_KEYWORD = 'performance'    # dropped unless the title also says 'free'
SADLERS_FREE_KEYWORD = KEYWORD_FREE
SADLERS_DESCRIPTION = "Community event at Sadler's Wells East."

# --- Copper Box Arena
COPPER_BOX_BASE_URL = "https://copperboxarena.org.uk"
COPPER_BOX_EVENTS_URL = COPPER_BOX_BASE_URL + "/events"
COPPER_BOX_DATE_FORMAT = "%b %d, %Y"
COPPER_BOX_EXCLUDED_TITLE_KEYWORDS = ['football', 'baller league', 'netball', 'pulse', 'london pulse']
COPPER_BOX_EXCLUDED_DESCRIPTION_KEYWORDS = ['football', 'netball']
COPPER_BOX_BASKETBALL_KEYWORDS = ['basketball', 'lions']
COPPER_BOX_NETBALL_KEYWORDS = ['netball', 'pulse']
COPPER_BOX_BOXING_KEYWORDS = ['boxing', 'fight']
SOURCE_COPPER_BOX = 'Copper Box Arena'

# --- St Bride's Church (scrapers/st_brides.py)
ST_BRIDES_BASE_URL = "https://www.stbrides.com"
ST_BRIDES_EVENTS_URL = ST_BRIDES_BASE_URL + "/whats-on/"
ST_BRIDES_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/14.0 Safari/605.1.15"
)
ST_BRIDES_EXCLUDE_PATTERN = (
    r'morning prayer|evensong|communion|eucharist|space for silence|compline|vespers|matins|bible|lent course'
)
ST_BRIDES_MUSIC_PATTERN = (
    r'recital|concert|piano|organ|choir|violin|cello|guitar|soprano|mezzo|tenor|baritone|bass|singers|'
    r'ensemble|quartet|trio|harp|flute|oboe|clarinet|trumpet|stabat|cantorum|scholars'
)
ST_BRIDES_MIN_TITLE_CHARS = 3
ST_BRIDES_MIN_TEXT_CHARS = 5
ST_BRIDES_LOCATION = "St Bride's Church, Fleet Street"
ST_BRIDES_DESCRIPTION = "Free lunchtime recital at St Bride's Church, Fleet Street"
SOURCE_ST_BRIDES = "St Bride's"

# --- St Stephen Walbrook (scrapers/st_stephen.py): NOT YET MOVED.
# Its venue text ends in a UK postcode and the privacy gate (private_data_scan, rule uk-postcode)
# blocks any commit that touches the file. Owner decision; until then the file keeps its own
# literals, listed with a reason in tests/params_literal_allowlist.txt.

# --- Tennis and padel at Lee Valley (scrapers/tennis.py)
TENNIS_BASE_URL = "https://www.better.org.uk"
TENNIS_URLS = [
    TENNIS_BASE_URL + "/leisure-centre/lee-valley/hockey-and-tennis-centre/news",
    "https://www.leevalleypark.org.uk/press-releases/lee-valley-hockey-and-tennis-centre-update",
]
TENNIS_TITLE_KEYWORDS = (LABEL_TENNIS.lower(), SUB_PADEL.lower())
TENNIS_DESCRIPTION_MAX_CHARS = 200
TENNIS_DATE_PLACEHOLDER = "See link"
SOURCE_TENNIS = 'Lea Valley Tennis'
# Weekly drop-in session that is always added to the report.
TENNIS_DROPIN_TITLE = "Women's Tennis Drop-In"
TENNIS_DROPIN_WEEKDAY = 3           # Thursday
TENNIS_DROPIN_HOUR = 10
TENNIS_DROPIN_MINUTE = 0
TENNIS_DROPIN_DATE_FORMAT = "%A, %d %B %Y"
TENNIS_DROPIN_LOCATION = "Lea Valley Hockey and Tennis Centre"
TENNIS_DROPIN_DESCRIPTION = "Weekly drop-in session. Check website for cancellations."
TENNIS_DROPIN_URL = (
    TENNIS_BASE_URL
    + "/leisure-centre/london/queen-elizabeth-olympic-park/lee-valley-hockey-and-tennis-centre/timetable"
)
TENNIS_DROPIN_PRICE = "£8.00 - £10.00"
TENNIS_DROPIN_SOURCE = 'Better / Lea Valley'

# --- TfL strikes (scrapers/tfl_strikes.py)
TFL_API_BASE = "https://api.tfl.gov.uk"
TFL_DISRUPTION_URL = TFL_API_BASE + "/Line/Mode/tube/Disruption"
TFL_STRIKES_URL = "https://tfl.gov.uk/campaign/strikes"
TFL_USER_AGENT = "StratfordEventsBot/1.0 (weekly personal report)"
TFL_LOOKAHEAD_DAYS = 7
TFL_STRIKE_KEYWORDS = ['strike', 'industrial action', 'walkout']
TFL_API_STRIKE_KEYWORDS = TFL_STRIKE_KEYWORDS + ['rmt', 'aslef', 'tssa']      # API text also names the unions
TFL_PAGE_STRIKE_KEYWORDS = TFL_STRIKE_KEYWORDS + ['disruption']
TFL_DESCRIPTION_MAX_CHARS = DESCRIPTION_MAX_CHARS
TFL_NO_STRIKES_TITLE = 'No tube strikes planned'
TFL_NO_STRIKES_DESCRIPTION = (
    'No industrial action affecting London Underground is currently planned for the coming week.'
)
TFL_NO_STRIKES_DATE_TEMPLATE = "Week of {date}"
TFL_RANGE_DATE_FORMAT = '%a %d %b'
TFL_API_TITLE_TEMPLATE = "🚇 Tube Strike: {lines}"
TFL_PAGE_TITLE_TEMPLATE = "🚇 {text}"
TFL_DEFAULT_DESCRIPTION = 'Industrial action planned.'
TFL_PAGE_DEFAULT_DESCRIPTION = 'See TfL website for details.'
TFL_DEFAULT_LINES = 'Multiple lines'
TFL_DATE_TBC = 'TBC'
SUB_TFL_STATUS = 'Status'
SUB_TFL_INDUSTRIAL_ACTION = 'Industrial Action'
SOURCE_TFL = 'TfL'
# (strptime format, regex) pairs tried in order on heading text.
TFL_HEADING_DATE_PATTERNS = [
    ("%d %B %Y", r'\d{1,2} \w+ \d{4}'),
    ("%d %B", r'\d{1,2} \w+'),
    ("%A %d %B", r'\w+ \d{1,2} \w+'),
]
TFL_NO_YEAR_PLACEHOLDER = 1900     # strptime year when the format has no year

# --- Stratford East theatre (scrapers/theatre.py)
THEATRE_BASE_URL = "https://www.stratfordeast.com"
THEATRE_EVENTS_URL = THEATRE_BASE_URL + "/whats-on"
THEATRE_DATE_FORMAT = "%a %d %b %Y"
THEATRE_FORBIDDEN_KEYWORDS = ['musical', 'dance', 'pantomime', 'panto', 'concert', 'music of']
SUB_THEATRE = SOURCE_STRATFORD_EAST

# --- UCL East (scrapers/ucl.py)
UCL_EVENTS_URL = (
    "https://cms-feed.ucl.ac.uk/s/search.json?collection=drupal-meta-events&meta_UclOrgUnit=%22UCL+East%22"
)
UCL_PUBLIC_AUDIENCE_KEYWORDS = ['public', 'everyone']
UCL_RESTRICTED_AUDIENCE_KEYWORDS = ['staff', 'student']
UCL_FORBIDDEN_KEYWORDS = ['dance', 'musical', 'ballet', 'opera']
# (sub-category, title keywords) tried in order; first match wins.
UCL_SUBCATEGORY_RULES = [
    ('Cinema', ['cinema', 'screening', 'film']),
    ('Exhibition', ['exhibition', 'gallery']),
    ('Lecture/Talk', ['lecture', 'talk', 'conversation']),
]
UCL_PRICE = "Free (usually)"
SOURCE_UCL = 'UCL East'

# --- V&A East (scrapers/va_east.py)
VA_BASE_URL = "https://www.vam.ac.uk"
VA_EVENTS_URL = VA_BASE_URL + "/whatson?venue=east-storehouse&venue=east-museum"
VA_VENUE_TEXTS = ['East', 'Storehouse']

# ---------------------------------------------------------------------------
# 7. Email (send_email.py). Credentials and the recipient are NOT here.
# ---------------------------------------------------------------------------
EMAIL_ENV_USERNAME_KEY = 'GMAIL_USERNAME'
EMAIL_ENV_PASSWORD_KEY = 'GMAIL_APP_PASSWORD'
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 465
EMAIL_FROM_NAME = "Stratford Events Bot"
EMAIL_SUBJECT_TEMPLATE = REPORT_TITLE + " - w/c {week_of}"
EMAIL_PLAINTEXT_FALLBACK = "Please enable HTML to view this report."

# ---------------------------------------------------------------------------
# 8. CI (read by .github/workflows/keepalive.yml)
# ---------------------------------------------------------------------------
KEEPALIVE_INACTIVE_DAYS = 50    # GitHub disables scheduled workflows after 60 days of inactivity