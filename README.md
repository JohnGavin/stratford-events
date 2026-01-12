# Stratford Events Weekly Reporter

A Python-based automated bot that scrapes and aggregates upcoming events in Stratford (E15/E20) and emails a weekly report via GitHub Actions.

## Project Criteria & Goals

*   **Focus Areas:**
    *   **Dining / Restaurants:** New openings, offers, and food news in Stratford/Westfield.
    *   **STEM / Factual:** Lectures, exhibitions, cinema, and workshops (e.g., UCL East, Here East).
    *   **Sports:** Non-football focus (e.g., Basketball at Copper Box, Tennis at Lea Valley/Stratford Park).
    *   **Culture:** Theatre plays (excluding musicals/dance).
    *   **Local Life:** Riverside East, East Village, and Westfield updates.
*   **Filters:**
    *   **Exclude:** Football, Musicals, Dance, Pantomime, Kids/Family-specific events, Women-only events.
    *   **Exclude:** Expired events (globally filtered, except recent news).
    *   **Exclude:** Non-public (Staff/Student only) UCL events.
*   **Sorting & Grouping:**
    *   Events are grouped by Category > Sub-category (e.g., Sports > Basketball).
    *   Events are sorted by Date (soonest first).
*   **Content:**
    *   Includes minimum adult price (no concessions).
    *   Full descriptions (no truncation).
    *   Clear location and date/time.

## Architecture

*   **Scrapers (`scrapers/`):** Modular Python scripts using `requests` and `BeautifulSoup`.
    *   `dining.py`: Fetches restaurant news and offers via Google News RSS.
    *   `aquatics.py`: Scrapes London Aquatics Centre events.
    *   `barbican.py`: Scrapes Barbican Centre (next 14 days only).
    *   `ucl.py`: Fetches from UCL East Funnelback API (JSON).
    *   `sports.py`: Scrapes Copper Box Arena.
    *   `gsmd.py`: Scrapes Guildhall School (East Bank only, next 14 days).
    *   `theatre.py`: Scrapes Stratford East.
    *   `qeop.py`: Scrapes Queen Elizabeth Olympic Park.
    *   `here_east.py`: Scrapes Here East.
    *   `tennis.py`: Generates recurring/static tennis info.
*   **Core Logic (`main.py`):**
    *   Orchestrates scrapers.
    *   Parses dates to `datetime` objects for sorting.
    *   Applies global deny-list filters.
    *   Groups events into categories/sub-categories.
    *   Renders HTML report using `jinja2`.
*   **Automation (`.github/workflows/`):**
    *   Runs weekly (Mondays @ 08:00 UTC) or on push.
    *   Sends email using a custom Python script (`send_email.py`) via Gmail SMTP.

## Setup

1.  **Secrets:** Set `GMAIL_USERNAME` and `GMAIL_APP_PASSWORD` in GitHub Repository Secrets.
2.  **Run:** Trigger manually via Actions tab or wait for schedule.

## Future Improvements

*   Dynamic scraping for Westfield/Restaurants (currently static).
*   More granular price extraction for complex ticketing sites.
