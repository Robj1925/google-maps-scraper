import re
import time
import datetime
import pandas as pd
import urllib.parse
import urllib.request
import os
import json
import argparse
from playwright.sync_api import sync_playwright

STATE_ABBR = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

def load_counties_data():
    local_path = os.path.join(os.path.dirname(__file__), "counties_by_state.json")
    if not os.path.exists(local_path):
        url = "https://raw.githubusercontent.com/balsama/us_counties_data/main/data/counties_by_state.json"
        print(f"📥 Local county database not found. Downloading US county lists dynamically from: {url}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                with open(local_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ Download complete! Database saved locally.")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to download counties database: {e}")
            
    with open(local_path, "r", encoding="utf-8") as f:
        return json.load(f)

def search_email_on_duckduckgo(name, search_query):
    clean_name = re.sub(r'[^\w\s]', '', name)
    query = f'"{clean_name}" {search_query} contact email'
    encoded_query = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    email = "N/A"
    try:
        req = urllib.request.Request(
            search_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            emails = re.findall(email_pattern, html)
            
            valid_emails = []
            for e in emails:
                lower_e = e.lower()
                if any(domain in lower_e for domain in ["duckduckgo.com", "google.com", "example.com", "w3.org", "sentry.io", "github.com"]):
                    continue
                if lower_e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                    continue
                valid_emails.append(e)
                
            if valid_emails:
                email = ", ".join(list(dict.fromkeys(valid_emails)))
    except Exception as e:
        print(f"Error searching email for {name}: {e}")
        
    return email

def clean_text(text):
    if not text:
        return "N/A"
    return re.sub(r'[\uE000-\uF8FF]', '', text).strip()

def scrape_google_maps(query, max_results=10, delay=2.0):
    leads = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            encoded_query = urllib.parse.quote_plus(query)
            search_url = f"https://www.google.com/maps/search/{encoded_query}"
            print(f"Navigating to {search_url}")
            page.goto(search_url)
            
            try:
                consent_button = page.locator('button:has-text("Accept all"), button:has-text("Reject all")').first
                if consent_button.count() > 0:
                    consent_button.click()
                    time.sleep(2)
            except Exception:
                pass
                
            print("Waiting for results...")
            page.wait_for_selector('a[href^="https://www.google.com/maps/place/"]', timeout=15000)
            
            feed_selector = 'div[role="feed"]'
            if page.locator(feed_selector).count() > 0:
                print("Scrolling feed to load more results...")
                for _ in range(15):
                    page.locator(feed_selector).evaluate("node => node.scrollBy(0, 1000)")
                    time.sleep(1)
            
            links = page.locator('a[href^="https://www.google.com/maps/place/"]').evaluate_all("nodes => nodes.map(n => n.href)")
            links = list(dict.fromkeys(links))
            print(f"Found {len(links)} places.")
            
            for url in links[:max_results]:
                try:
                    page.goto(url)
                    page.wait_for_selector('h1', timeout=5000)
                    
                    name = page.locator('h1').first.text_content().strip()
                    
                    website_locator = page.locator('a[data-item-id="authority"], a[aria-label^="Website"]')
                    if website_locator.count() > 0:
                        print(f"Skipping {name} - has website")
                        continue
                        
                    phone_locator = page.locator('button[data-item-id^="phone:"]')
                    phone = clean_text(phone_locator.first.text_content()) if phone_locator.count() > 0 else "N/A"
                    
                    address_locator = page.locator('button[data-item-id="address"]')
                    address = clean_text(address_locator.first.text_content()) if address_locator.count() > 0 else "N/A"
                    
                    print(f"Lead found: {name}. Searching for email...")
                    email = search_email_on_duckduckgo(name, query)
                    print(f"Email for {name}: {email}")
                    
                    leads.append({
                        'Name': name,
                        'Phone': phone,
                        'Address': address,
                        'Email': email,
                        'URL': url
                    })
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                finally:
                    time.sleep(delay)

        except Exception as e:
            print(f"Main error: {e}")
            screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            screenshot_path = os.path.join(screenshot_dir, f"error_{timestamp}.png")
            page.screenshot(path=screenshot_path)
            print(f"🖼️ Saved error screenshot to {screenshot_path}")

        finally:
            browser.close()
            
    return leads

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="High-performance U.S. Google Maps & DuckDuckGo Email Scraper for Lead Generation")
    parser.add_argument("--industry", type=str, help="Industry to target (e.g. roofing, construction, plumbing)")
    parser.add_argument("--state", type=str, help="Target U.S. state for county-wide search (supports 2-letter abbreviation or full name)")
    parser.add_argument("--counties", type=str, help="Comma-separated custom locations or counties to target")
    parser.add_argument("--max-results", type=int, default=10, help="Max results to scrape per query (default: 10)")
    parser.add_argument("--delay", type=float, default=2.0, help="Pause in seconds between individual place pages (default: 2.0). Lowering this increases your risk of being rate-limited or blocked, and is inconsiderate to the sites you are crawling.")
    parser.add_argument("--query", type=str, help="Direct search query to send to Google Maps (bypasses county/state lists)")
    parser.add_argument("--csv", type=str, default="leads.csv", help="Output CSV path (default: leads.csv)")
    
    args = parser.parse_args()
    
    if not args.query and not args.industry:
        parser.error("You must specify either --query or --industry")
        
    queries = []
    if args.query:
        queries.append(args.query)
    else:
        locations = []
        if args.counties:
            locations = [loc.strip() for loc in args.counties.split(",")]
        elif args.state:
            # Load database dynamically
            counties_data = load_counties_data()
            
            # Resolve state input format
            state_input = args.state.upper() if len(args.state) == 2 else args.state.strip().title()
            resolved_state = STATE_ABBR.get(state_input, state_input)
            
            if resolved_state not in counties_data:
                parser.error(f"State '{args.state}' not found in the U.S. counties database. Please verify name or abbreviation.")
                
            # Extract county list from the parsed database
            locations = list(counties_data[resolved_state].keys())
            print(f"📋 Loaded {len(locations)} counties for the state of {resolved_state}.")
        else:
            parser.error("You must specify either --state, --counties, or --query")
            
        for loc in locations:
            queries.append(f"{args.industry} in {loc}")
            
    csv_file = args.csv
    all_leads = []
    seen_phones = set()
    seen_urls = set()
    
    if os.path.exists(csv_file):
        try:
            df_existing = pd.read_csv(csv_file)
            all_leads = df_existing.to_dict('records')
            for lead in all_leads:
                url = lead.get('URL')
                phone = lead.get('Phone')
                if pd.notna(url):
                    seen_urls.add(str(url))
                if pd.notna(phone) and str(phone) != 'N/A' and str(phone) != '':
                    seen_phones.add(str(phone))
            print(f"📖 Loaded {len(all_leads)} existing leads from {csv_file} for deduplication.")
        except Exception as e:
            print(f"⚠️ Error loading existing CSV: {e}. Starting fresh.")
            
    total_count = len(queries)
    current_idx = 0
    
    for query in queries:
        current_idx += 1
        print(f"\n🚀 Starting scrape [{current_idx}/{total_count}]: {query}")
        
        leads = scrape_google_maps(query, max_results=args.max_results, delay=args.delay)
        
        new_leads_added = 0
        for lead in leads:
            url = lead.get('URL')
            phone = lead.get('Phone')
            
            if url in seen_urls or (phone != 'N/A' and phone in seen_phones):
                continue
                
            seen_urls.add(url)
            if phone != 'N/A':
                seen_phones.add(phone)
            all_leads.append(lead)
            new_leads_added += 1
            
        if new_leads_added > 0:
            df = pd.DataFrame(all_leads)
            df.to_csv(csv_file, index=False)
            print(f"💾 Incremental save: Added {new_leads_added} new leads. Total is now {len(all_leads)} in {csv_file}")
        else:
            print("ℹ️ No new unique leads found for this query.")
            
        if current_idx < total_count:
            print("⏳ Sleeping 5 seconds before next query...")
            time.sleep(5)
            
    print(f"\n🎉 Successfully finished all scraping campaigns! Total compiled and deduplicated: {len(all_leads)} leads in {csv_file}")
