import os
import datetime
from jinja2 import Environment, FileSystemLoader
from utils.common import apply_date_window
from scrapers.qeop import fetch_qeop_events
from scrapers.ucl import fetch_ucl_events
from scrapers.sports import fetch_copper_box_events
from scrapers.theatre import fetch_stratford_east_events
from scrapers.here_east import fetch_here_east_events
from scrapers.tennis import fetch_tennis_events
from scrapers.va_east import fetch_va_events
from scrapers.sadlers import fetch_sadlers_events
from scrapers.gsmd import fetch_gsmd_events
from scrapers.tfl_strikes import fetch_tfl_strikes
from scrapers.alerts import fetch_google_alerts
from scrapers.dining import fetch_dining_news
from scrapers.aquatics import fetch_aquatics_events
from scrapers.barbican import fetch_barbican_events
from scrapers.lso import fetch_lso_events
from scrapers.barts_north_wing import fetch_barts_north_wing_events
from scrapers.st_brides import fetch_st_brides_events
from scrapers.great_st_barts import fetch_great_st_barts_events
from scrapers.st_stephen import fetch_st_stephen_events
from params import (
    CATEGORY_FREE_CONCERTS,
    CATEGORY_ORDER,
    CATEGORY_OTHER,
    CATEGORY_SPORTS,
    FREE_RECATEGORIZE_SOURCES,
    GLOBAL_FORBIDDEN_KEYWORDS,
    GOOGLE_NEWS_ITEMS_PER_SUBCATEGORY,
    PRICE_FREE,
    REPORT_OUTPUT_FILE,
    REPORT_TAGLINE,
    REPORT_TEMPLATE_FILE,
    REPORT_TITLE,
    REPORT_TODAY_FORMAT,
    SCRAPER_LABELS,
    SOURCE_GOOGLE_NEWS,
    SPORTS_SINGLE_ITEM_LIMIT,
    SPORTS_SINGLE_ITEM_SUBCATEGORIES,
    SPORTS_SUBCATEGORY_PRIORITY,
    SUB_GENERAL,
    UNDATED_SORT_TIMESTAMP,
)

def main():
    print("Starting event collection...")
    
    all_events = []
    
    # Fetch from all sources
    # (Error handling wrapped in individual calls mostly, but good to keep safe here)
    scrapers = [
        (fetch_tfl_strikes, SCRAPER_LABELS['tfl_strikes']),  # FIRST — appears at top of report
        (fetch_qeop_events, SCRAPER_LABELS['qeop']),
        (fetch_ucl_events, SCRAPER_LABELS['ucl']),
        (fetch_copper_box_events, SCRAPER_LABELS['sports']),
        (fetch_stratford_east_events, SCRAPER_LABELS['theatre']),
        (fetch_here_east_events, SCRAPER_LABELS['here_east']),
        (fetch_tennis_events, SCRAPER_LABELS['lea_valley']),
        (fetch_va_events, SCRAPER_LABELS['va_east']),
        (fetch_sadlers_events, SCRAPER_LABELS['sadlers']),
        (fetch_gsmd_events, SCRAPER_LABELS['gsmd']),
        (fetch_google_alerts, SCRAPER_LABELS['news']),
        (fetch_dining_news, SCRAPER_LABELS['dining']),
        (fetch_aquatics_events, SCRAPER_LABELS['aquatics']),
        (fetch_barbican_events, SCRAPER_LABELS['barbican']),
        (fetch_lso_events, SCRAPER_LABELS['lso']),
        (fetch_barts_north_wing_events, SCRAPER_LABELS['barts_north_wing']),
        (fetch_st_brides_events, SCRAPER_LABELS['st_brides']),
        (fetch_great_st_barts_events, SCRAPER_LABELS['great_st_barts']),
        (fetch_st_stephen_events, SCRAPER_LABELS['st_stephen'])
    ]
    
    for scraper_func, name in scrapers:
        try:
            print(f"Fetching {name} events...")
            events = scraper_func()
            # Ensure source is set if missing
            for e in events: 
                if 'source' not in e: e['source'] = name
            all_events.extend(events)
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    # Shared date window (issue #8): untitled rows, past rows, rows beyond the
    # horizon and stale news are dropped; every kept row gets one date format.
    window = apply_date_window(all_events)
    print(window.summary())

    # Deduplicate and Clean
    unique_events = {}
    for e in window.kept:
        key = e['title'].strip().lower()
        if key not in unique_events:
            unique_events[key] = e

    # Final Filter (Global)
    filtered_events = []
    forbidden = GLOBAL_FORBIDDEN_KEYWORDS
    
    for e in unique_events.values():
        text = (e['title'] + " " + e.get('description', '')).lower()
        if any(word in text for word in forbidden):
            continue

        # Recategorize Free events from specific sources
        if e.get('source') in FREE_RECATEGORIZE_SOURCES:
            if e.get('price') == PRICE_FREE:
                e['category'] = CATEGORY_FREE_CONCERTS

        # Ensure sub_category exists
        if 'sub_category' not in e:
            e['sub_category'] = SUB_GENERAL
            
        filtered_events.append(e)

    # Sort by Date (Future first, None/Undated last)
    def sort_key(e):
        d = e.get('date_obj')
        if d: return d.timestamp()
        return UNDATED_SORT_TIMESTAMP # Far future for undated
        
    filtered_events.sort(key=sort_key)

    # Grouping Structure: Category -> SubCategory -> [Events]
    # We want a dictionary of dictionaries
    grouped_events = {}
    
    # Define preferred category order
    cat_order = CATEGORY_ORDER
    
    for e in filtered_events:
        cat = e.get('category', CATEGORY_OTHER)
        sub = e.get('sub_category', SUB_GENERAL)
        
        if cat not in grouped_events:
            grouped_events[cat] = {}
        if sub not in grouped_events[cat]:
            grouped_events[cat][sub] = []
            
        grouped_events[cat][sub].append(e)

    # Post-Processing: Limit specific sub-categories
    # Basketball and Boxing: Show only the next upcoming event
    if CATEGORY_SPORTS in grouped_events:
        for sub in SPORTS_SINGLE_ITEM_SUBCATEGORIES:
            if sub in grouped_events[CATEGORY_SPORTS]:
                grouped_events[CATEGORY_SPORTS][sub] = grouped_events[CATEGORY_SPORTS][sub][:SPORTS_SINGLE_ITEM_LIMIT]

    # Limit Google News items to 1 per sub-category
    for cat in grouped_events:
        for sub in grouped_events[cat]:
            events_list = grouped_events[cat][sub]
            # Check if this list contains Google News items
            # (Assuming a list is either all Google News or not, or mixed. 
            # If mixed, we filter only the Google News ones? 
            # Simpler: If the first item is Google News, limit list to 1.
            # Or iterate and count.
            # User said: "filter 'google news' source to only show their top hit")
            
            # Separate Google News items from others (if any mixed)
            gnews = [e for e in events_list if e.get('source') == SOURCE_GOOGLE_NEWS]
            others = [e for e in events_list if e.get('source') != SOURCE_GOOGLE_NEWS]
            
            if gnews:
                # Keep only top 1 Google News item
                gnews = gnews[:GOOGLE_NEWS_ITEMS_PER_SUBCATEGORY]
                # Recombine (put GNews first or last? Date sorted usually. 
                # If we split, we break sort.
                # Better: Filter in place or slice)
                
                # If the whole list is Google News (typical for Dining/News categories)
                if not others:
                    grouped_events[cat][sub] = gnews
                else:
                    # Mixed source. Re-sort might be needed but main list was date sorted.
                    # We just want to reduce the GNews count.
                    # Let's keep others and add 1 GNews.
                    new_list = others + gnews
                    # Re-sort by date just in case
                    # We need the sort key function again or lambda
                    new_list.sort(key=lambda e: e.get('date_obj').timestamp() if e.get('date_obj') else UNDATED_SORT_TIMESTAMP)
                    grouped_events[cat][sub] = new_list

    # Reorder Sports sub-categories: Tennis, Padel, then others
    if CATEGORY_SPORTS in grouped_events:
        sports_dict = grouped_events[CATEGORY_SPORTS]
        ordered_sports = {}
        # Priority keys
        for key in SPORTS_SUBCATEGORY_PRIORITY:
            if key in sports_dict:
                ordered_sports[key] = sports_dict.pop(key)
        # Remaining keys (alphabetical or date sorted? currently date sorted by insertion)
        ordered_sports.update(sports_dict)
        grouped_events[CATEGORY_SPORTS] = ordered_sports

    # Generate Report
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template(REPORT_TEMPLATE_FILE)
    
    output = template.render(
        grouped_events=grouped_events,
        category_order=cat_order,
        report_title=REPORT_TITLE,
        report_tagline=REPORT_TAGLINE,
        today=datetime.date.today().strftime(REPORT_TODAY_FORMAT)
    )
    
    with open(REPORT_OUTPUT_FILE, 'w') as f:
        f.write(output)
        
    print(f"Report generated: {REPORT_OUTPUT_FILE} ({len(filtered_events)} events found)")

if __name__ == "__main__":
    main()
