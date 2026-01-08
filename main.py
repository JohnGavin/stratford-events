import os
import datetime
from jinja2 import Environment, FileSystemLoader
from scrapers.qeop import fetch_qeop_events
from scrapers.ucl import fetch_ucl_events
from scrapers.sports import fetch_copper_box_events
from scrapers.theatre import fetch_stratford_east_events
from scrapers.here_east import fetch_here_east_events
from scrapers.tennis import fetch_tennis_events

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
        (fetch_tennis_events, "Tennis")
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

    # Add Static / Informational Sections for Hard-to-Scrape Targets
    # Westfield Shopping Centre
    all_events.append({
        'title': "Westfield Stratford City Events & Offers",
        'date_str': "Ongoing",
        'date_obj': datetime.datetime.now() + datetime.timedelta(days=365), # Always future
        'location': "Westfield Stratford City",
        'description': "Check the official 'What's On' page for pop-up shops, cinema screenings, and seasonal events.",
        'url': "https://uk.westfield.com/stratfordcity/events",
        'category': 'Westfield / Shopping',
        'sub_category': 'General',
        'price': "Varies",
        'source': 'Static Link'
    })
    
    # Restaurants / East Village
    all_events.append({
        'title': "East Village: Eat, Drink, Shop",
        'date_str': "Ongoing",
        'date_obj': datetime.datetime.now() + datetime.timedelta(days=365),
        'location': "East Village E20",
        'description': "Explore new restaurant openings and events in the former Athletes' Village.",
        'url': "https://www.eastvillagelondon.co.uk/whats-on",
        'category': 'East Village',
        'sub_category': 'Dining & Events',
        'price': "Varies",
        'source': 'Static Link'
    })


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
        'women', 'woman', 'ladies', 'kid', 'child', 'junior', 'boy', 'girl', 'family'
    ]
    
    # Use timezone-aware UTC now for comparison if possible, or naive if dates are naive
    # Safest is to handle both.
    now = datetime.datetime.now().astimezone()
    
    for e in unique_events.values():
        text = (e['title'] + " " + e.get('description', '')).lower()
        if any(word in text for word in forbidden):
            continue
        
        # Date Filter: Exclude past events
        # Events with no date_obj (None) are kept (assume 'See website' or 'Ongoing')
        if e.get('date_obj'):
            dt = e['date_obj']
            # Make naive datetimes aware (assume local/system time)
            if dt.tzinfo is None:
                dt = dt.astimezone()
                
            if dt < now:
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
    cat_order = ['STEM / Factual', 'Sports', 'Theatre', 'Tennis', 'Riverside East', 'East Village', 'Westfield / Shopping', 'Other']
    
    for e in filtered_events:
        cat = e.get('category', 'Other')
        sub = e.get('sub_category', 'General')
        
        if cat not in grouped_events:
            grouped_events[cat] = {}
        if sub not in grouped_events[cat]:
            grouped_events[cat][sub] = []
            
        grouped_events[cat][sub].append(e)

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
