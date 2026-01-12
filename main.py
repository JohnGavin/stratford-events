import os
import datetime
from jinja2 import Environment, FileSystemLoader
from scrapers.qeop import fetch_qeop_events
from scrapers.ucl import fetch_ucl_events
from scrapers.sports import fetch_copper_box_events
from scrapers.theatre import fetch_stratford_east_events
from scrapers.here_east import fetch_here_east_events
from scrapers.tennis import fetch_tennis_events
from scrapers.va_east import fetch_va_events
from scrapers.sadlers import fetch_sadlers_events
from scrapers.gsmd import fetch_gsmd_events
from scrapers.alerts import fetch_google_alerts
from scrapers.dining import fetch_dining_news
from scrapers.aquatics import fetch_aquatics_events
from scrapers.barbican import fetch_barbican_events

def main():
    print("Starting event collection...")
    
    all_events = []
    
    # Fetch from all sources
    # (Error handling wrapped in individual calls mostly, but good to keep safe here)
    scrapers = [
        (fetch_qeop_events, "QEOP"),
        (fetch_ucl_events, "UCL"),
        (fetch_copper_box_events, "Sports"),
        (fetch_stratford_east_events, "Theatre"),
        (fetch_here_east_events, "Here East"),
        (fetch_tennis_events, "Tennis"),
        (fetch_va_events, "V&A East"),
        (fetch_sadlers_events, "Sadler's Wells"),
        (fetch_gsmd_events, "Guildhall School"),
        (fetch_google_alerts, "News"),
        (fetch_dining_news, "Dining & Offers"),
        (fetch_aquatics_events, "Aquatics"),
        (fetch_barbican_events, "Barbican")
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

    # Deduplicate and Clean
    unique_events = {}
    for e in all_events:
        key = e['title'].strip().lower()
        if key not in unique_events:
            unique_events[key] = e
            
    # Final Filter (Global)
    filtered_events = []
    forbidden = [
        'football', 'musical', 'dance', 'pantomime', 'panto', 'ballet', 'opera',
        'women', 'woman', 'ladies', 'kid', 'child', 'junior', 'boy', 'girl', 'family',
        'netball'
    ]
    
    # Use timezone-aware UTC now for comparison if possible, or naive if dates are naive
    # Safest is to handle both.
    now = datetime.datetime.now().astimezone()
    
    for e in unique_events.values():
        text = (e['title'] + " " + e.get('description', '')).lower()
        if any(word in text for word in forbidden):
            continue
        
        # Date Filter: STRICT - Must have date_obj
        if not e.get('date_obj'):
            # Drop events without a valid parsed date
            continue
            
        dt = e['date_obj']
        if dt.tzinfo is None:
            dt = dt.astimezone()
            
        # Allow recent news/offers even if in the past
        is_news = e.get('category') in ['News & Alerts', 'Dining & Offers']
        if dt < now and not is_news:
            continue
        
        # Ensure sub_category exists
        if 'sub_category' not in e:
            e['sub_category'] = 'General'
            
        filtered_events.append(e)

    # Sort by Date (Future first, None/Undated last)
    def sort_key(e):
        d = e.get('date_obj')
        if d: return d.timestamp()
        return 9999999999.0 # Far future for undated
        
    filtered_events.sort(key=sort_key)

    # Grouping Structure: Category -> SubCategory -> [Events]
    # We want a dictionary of dictionaries
    grouped_events = {}
    
    # Define preferred category order
    cat_order = ['Dining & Offers', 'STEM / Factual', 'Theatre', 'Tennis', 'Riverside East', 'East Village', 'Westfield / Shopping', 'Community', 'News & Alerts', 'Other', 'Sports']
    
    for e in filtered_events:
        cat = e.get('category', 'Other')
        sub = e.get('sub_category', 'General')
        
        if cat not in grouped_events:
            grouped_events[cat] = {}
        if sub not in grouped_events[cat]:
            grouped_events[cat][sub] = []
            
        grouped_events[cat][sub].append(e)

    # Post-Processing: Limit specific sub-categories
    # Basketball and Boxing: Show only the next upcoming event (events are already sorted by date)
    if 'Sports' in grouped_events:
        for sub in ['Basketball', 'Boxing']:
            if sub in grouped_events['Sports']:
                grouped_events['Sports'][sub] = grouped_events['Sports'][sub][:1]
                
    # Reorder Sports sub-categories: Tennis, Padel, then others
    if 'Sports' in grouped_events:
        sports_dict = grouped_events['Sports']
        ordered_sports = {}
        # Priority keys
        for key in ['Tennis', 'Padel']:
            if key in sports_dict:
                ordered_sports[key] = sports_dict.pop(key)
        # Remaining keys (alphabetical or date sorted? currently date sorted by insertion)
        ordered_sports.update(sports_dict)
        grouped_events['Sports'] = ordered_sports

    # Generate Report
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('report_template.html')
    
    output = template.render(
        grouped_events=grouped_events,
        category_order=cat_order,
        today=datetime.date.today().strftime("%d %B %Y")
    )
    
    with open('report.html', 'w') as f:
        f.write(output)
        
    print(f"Report generated: report.html ({len(filtered_events)} events found)")

if __name__ == "__main__":
    main()
