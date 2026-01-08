import datetime

def fetch_tennis_events():
    events = []
    today = datetime.date.today()
    
    # 1. Lea Valley Hockey and Tennis Centre (Static/Recurring)
    # Based on search results: Women's Drop-in on Thursdays 10:00
    
    # Calculate next Thursday
    days_ahead = 3 - today.weekday() # Thursday is 3
    if days_ahead <= 0: days_ahead += 7
    next_thursday = today + datetime.timedelta(days=days_ahead)
    
    # Combine with time 10:00 for sorting
    next_thursday_dt = datetime.datetime.combine(next_thursday, datetime.time(10, 0))
    
    events.append({
        'title': "Women's Tennis Drop-In",
        'date_str': next_thursday.strftime("%A, %d %B %Y") + " @ 10:00",
        'date_obj': next_thursday_dt,
        'location': "Lea Valley Hockey and Tennis Centre",
        'description': "Weekly drop-in session. Check website for cancellations.",
        'url': "https://www.better.org.uk/leisure-centre/london/queen-elizabeth-olympic-park/lee-valley-hockey-and-tennis-centre/timetable",
        'category': 'Sports',
        'sub_category': 'Tennis',
        'price': "£8.00 (approx)",
        'source': 'Better / Lea Valley'
    })
    
    # Static info
    events.append({
        'title': "Lea Valley Tennis Courts & Courses",
        'date_str': "Daily",
        'date_obj': datetime.datetime.combine(today, datetime.time(23, 59)), # Push to end
        'location': "Lea Valley Hockey and Tennis Centre",
        'description': "Indoor and outdoor courts available for booking. Adult and Junior coaching courses running.",
        'url': "https://www.better.org.uk/leisure-centre/london/queen-elizabeth-olympic-park/lee-valley-hockey-and-tennis-centre",
        'category': 'Sports',
        'sub_category': 'Tennis',
        'price': "Varies",
        'source': 'Better / Lea Valley'
    })

    # 2. Stratford Park (West Ham Lane)
    events.append({
        'title': "Stratford Park Tennis Courts (Booking)",
        'date_str': "Open Daily",
        'date_obj': datetime.datetime.combine(today, datetime.time(23, 59)),
        'location': "Stratford Park (West Ham Lane)",
        'description': "Community tennis courts managed by Better/LTA. Book online via ClubSpark.",
        'url': "https://clubspark.lta.org.uk/StratfordPark/Booking",
        'category': 'Sports',
        'sub_category': 'Tennis',
        'price': "Free / Low Cost",
        'source': 'ClubSpark / LTA'
    })

    return events

if __name__ == "__main__":
    events = fetch_tennis_events()
    for e in events:
        print(f"Title: {e['title']}\nDate: {e['date_str']}\nURL: {e['url']}\n---")

