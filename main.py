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
    try:
        print("Fetching Here East events...")
        he = fetch_here_east_events()
        all_events.extend(he)
    except Exception as e:
        print(f"Error fetching Here East: {e}")

    try:
        print("Fetching QEOP events...")
        qeop = fetch_qeop_events()
        for e in qeop: e['source'] = 'QEOP'
        all_events.extend(qeop)
    except Exception as e:
        print(f"Error fetching QEOP: {e}")

    try:
        print("Fetching UCL events...")
        ucl = fetch_ucl_events()
        all_events.extend(ucl)
    except Exception as e:
        print(f"Error fetching UCL: {e}")

    try:
        print("Fetching Sports events...")
        sports = fetch_copper_box_events()
        all_events.extend(sports)
    except Exception as e:
        print(f"Error fetching Sports: {e}")

    try:
        print("Fetching Theatre events...")
        theatre = fetch_stratford_east_events()
        all_events.extend(theatre)
    except Exception as e:
        print(f"Error fetching Theatre: {e}")

    try:
        print("Fetching Tennis events...")
        tennis = fetch_tennis_events()
        all_events.extend(tennis)
    except Exception as e:
        print(f"Error fetching Tennis: {e}")

    # Deduplicate and Clean
    unique_events = {}
    for e in all_events:
        # Use title as a simple key for deduplication
        key = e['title'].strip().lower()
        if key not in unique_events:
            unique_events[key] = e
            
    # Final Filter (Global)
    filtered_events = []
    forbidden = [
        'football', 'musical', 'dance', 'pantomime', 'panto', 'ballet', 'opera',
        'women', 'woman', 'ladies', 'kid', 'child', 'junior', 'boy', 'girl', 'family'
    ]
    
    for e in unique_events.values():
        text = (e['title'] + " " + e.get('description', '')).lower()
        if any(word in text for word in forbidden):
            continue
            
        # Assign category if missing
        if 'category' not in e or not e['category']:
            if 'UCL' in e['source']: e['category'] = 'STEM/Factual'
            elif 'Here East' in e['source']: e['category'] = 'STEM/Factual'
            elif 'Theatre' in e['title'] or 'Stratford East' in e['source']: e['category'] = 'Theatre'
            elif 'Tennis' in e['title'] or 'Tennis' in e.get('category', ''): e['category'] = 'Tennis'
            elif 'Sports' in e.get('category', ''): e['category'] = 'Sports'
            else: e['category'] = 'General/Other'
            
        filtered_events.append(e)

    # Group by category
    events_by_category = {
        'STEM / Factual': [],
        'Tennis': [],
        'Sports': [],
        'Theatre': [],
        'Other / Community': []
    }
    
    for e in filtered_events:
        cat = e.get('category', 'General/Other')
        if 'STEM' in cat: events_by_category['STEM / Factual'].append(e)
        elif 'Tennis' in cat: events_by_category['Tennis'].append(e)
        elif 'Sports' in cat: events_by_category['Sports'].append(e)
        elif 'Theatre' in cat: events_by_category['Theatre'].append(e)
        else: events_by_category['Other / Community'].append(e)

    # Generate Report
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('report_template.html')
    
    output = template.render(
        events_by_category=events_by_category,
        today=datetime.date.today().strftime("%B %d, %Y")
    )
    
    with open('report.html', 'w') as f:
        f.write(output)
        
    print(f"Report generated: report.html ({len(filtered_events)} events found)")

if __name__ == "__main__":
    main()
