# 🚀 Google Maps Lead Scraper & Contact Finder

A professional, high-speed Python command-line utility that extracts local business prospects directly from Google Maps without requiring API keys or quota fees. 

The scraper targets businesses **lacking website links** (your ideal candidates for free website builds or modern design outreach), retrieves their public contact information, searches DuckDuckGo for their company contact email addresses, and persists results incrementally with automatic deduplication.

---

## 📖 Table of Contents
1. [System Features](#-system-features)
2. [Prerequisites & System Requirements](#-prerequisites--system-requirements)
3. [Step-by-Step Installation](#-step-by-step-installation)
4. [Comprehensive Usage Examples](#-comprehensive-usage-examples)
5. [Understanding the Output Data Schema](#-understanding-the-output-data-schema)
6. [Data Sources & Attribution](#-data-sources--attribution)
7. [Legal & Responsible Use](#️-legal--responsible-use)
8. [Troubleshooting & FAQs](#-troubleshooting--faqs)
9. [License](#-license)

---

## 🔍 System Features

* **Zero Maps API Fees**: Leverages Playwright to scrape public Google Maps results in headless Chromium.
* **Smart Filter**: Automatically skips any local listing that already has an established website link.
* **DuckDuckGo Email Locator**: Searches public indexing dynamically for the company's contact email address.
* **Incremental Saving & Deduplication**: Saves lists progressively after every query to protect data and guarantees zero duplicates via URL and phone hashing.
* **Self-Healing County Database**: Ships with (and can re-download) a local list of 3,048 counties covering the 50 U.S. states, for seamless state-wide target queries. Note the database covers the 50 states only: Washington D.C. and the U.S. territories are not included, so target those with `--counties` or `--query` instead.
* **Highly Customizable CLI**: Run campaigns easily across predefined state arrays, custom county list strings, or custom search queries.

---

## 💻 Prerequisites & System Requirements

* **Operating System**: macOS, Linux, or Windows (tested and optimized for macOS & Linux environments).
* **Python**: **Python 3.11 or newer is required.** pandas 3.x dropped support for anything below 3.11. Verified working on Python 3.14.
  * macOS ships a system `python3` that is still 3.9, which will **not** work. Install a modern interpreter first: `brew install python@3.12` (or newer) and build your virtual environment from that binary.
* **Node.js** (Optional): Only required if connecting to the downstream SMS outreach client.

---

## 🛠️ Step-by-Step Installation

Follow these exact steps to set up your local environment and download the headless browser binaries.

### Step 1: Clone the Repository
Clone the repository and navigate into the project directory:
```bash
git clone https://github.com/Robj1925/google-maps-scraper.git
cd google-maps-scraper
```

### Step 2: Initialize Virtual Environment
Isolate your Python dependencies using a local virtual environment.
```bash
# Create a virtual environment named "venv" using the system python3
python3 -m venv venv

# Activate the virtual environment
# On macOS and Linux:
source venv/bin/activate

# On Windows (Command Prompt):
# venv\Scripts\activate.bat

# On Windows (PowerShell):
# venv\Scripts\Activate.ps1
```

### Step 3: Install Required Libraries
Upgrade pip and install the mandatory Python packages (`playwright` and `pandas`):
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Install Headless Playwright Browser
Download and configure the headless Chromium binary required for crawling Google Maps:
```bash
playwright install chromium
```

---

## 🚀 Comprehensive Usage Examples

Execute campaigns dynamically by running commands inside your active virtual environment.

**No API keys and no `.env` file are needed.** The scraper reads no environment variables at all: everything is driven by CLI flags.

### Example 1: Direct Maps Query (start here)
The fastest way to try the tool. A single search query runs directly against Google Maps and bypasses the state and county loops entirely:
```bash
# Search for hair salons specifically in Salem, NY
python scraper.py --query "hair salons in Salem, NY" --max-results 5
```

> [!WARNING]
> **Read this before running a full-state campaign.**
> A state-wide run is not a quick job. `--state TX` expands to 254 separate county queries. Each query loads a Google Maps search page, scrolls the results feed roughly 15 times, then opens every matching place page individually, and each lead that passes the no-website filter also triggers a DuckDuckGo lookup. That is on the order of 16+ page loads per county before per-lead traffic, so a full state means **hours of continuous automated requests** from your IP.
>
> Sustained volume like that is the fastest route to a CAPTCHA wall or a temporary block, and it is a real load on someone else's servers. Start narrow with `--query` or `--counties`, keep `--max-results` low, and leave `--delay` at its default (or raise it). Run a whole state only when you actually need it.

### Example 2: State-Wide County Campaign
Crawl an entire state's counties for a specific sector. The script resolves state abbreviations or full names automatically and uses the bundled `counties_by_state.json` offline:
```bash
# Scrape roofing contractors across all 254 counties in Texas
python scraper.py --industry "roofing" --state TX

# Scrape construction companies across all 62 counties in New York
python scraper.py --industry "construction" --state "New York"

# Scrape plumbing services across all 21 counties in New Jersey
python scraper.py --industry "plumbing" --state NJ
```

### Example 3: Target Custom Counties list
To scrape only specific counties or municipal regions, pass a comma-separated list to the `--counties` flag:
```bash
# Scrape landscaping businesses in specific counties of New Jersey and New York
python scraper.py --industry "landscaping" --counties "Bergen County NJ, Orange County NY, Westchester County NY"
```

### Example 4: Limit Results per Query
Control your crawl speed and resource consumption by specifying the max results to fetch per location loop using `--max-results` (default is 10):
```bash
# Get at most 3 electrical contractors per county in New Jersey
python scraper.py --industry "electrician" --state NJ --max-results 3
```

### Example 5: Custom Output CSV File
Specify a custom destination CSV file path using `--csv` (default is `leads.csv`):
```bash
# Save scraped roofing leads to a distinct target sheet
python scraper.py --industry "roofing" --state NJ --csv "new_jersey_roofers.csv"
```

### Example 6: Adjust the Pause Between Place Pages
`--delay` sets the pause in seconds between individual place pages (default is `2.0`). The default is deliberately conservative. Raising it is safe, lowering it is not:
```bash
# Go slower and gentler on a long campaign
python scraper.py --industry "roofing" --state NJ --delay 5
```

---

## 📊 Understanding the Output Data Schema

All scraped leads are appended progressively to your output CSV file. The CSV contains the following columns:

| Column Name | Example Value | Description |
| :--- | :--- | :--- |
| **`Name`** | `Example Roofing Co` | The public business name listed on Google Maps. |
| **`Phone`** | `(555) 010-0000` | The public phone number listed on Google Maps (not validated). |
| **`Address`** | `123 Main St, Springfield, IL 62701` | The public street address of the business. |
| **`Email`** | `info@example.com` | Scraped email address from DuckDuckGo contact index (`N/A` if not found). |
| **`URL`** | `https://www.google.com/maps/place/...` | The direct Google Maps page link (used for indexing/deduplication). |

---

## 📚 Data Sources & Attribution

The bundled `counties_by_state.json` county database is not original work. It comes from the open **[balsama/us_counties_data](https://github.com/balsama/us_counties_data)** project, and the scraper re-downloads it from that repository if the local copy is missing (see the URL in `scraper.py`). Full credit to that project and its contributors.

If you redistribute this tool or the county data with it, check the upstream repository's own license and terms first. They govern that file, not the MIT license below.

---

## ⚖️ Legal & Responsible Use

This tool automates access to public web pages. That does not make every use of it lawful or permitted. Read this section before you run it.

* **Google's Terms of Service.** Scraping Google Maps may violate Google's Terms of Service, regardless of whether the data itself is public. Google also offers a paid Places API for programmatic access. You are solely responsible for deciding whether your use is acceptable, and for any consequence of that decision, including IP blocks or account action.
* **The data you collect is regulated.** Business names, phone numbers, email addresses, and street addresses are contact data, and using them for outreach is governed by law in most places. Depending on your jurisdiction and the recipient's, that can include **CAN-SPAM** (commercial email in the U.S.), the **TCPA** (calls and SMS in the U.S., including to numbers on the National Do Not Call Registry), and the **GDPR** or equivalent regimes (anywhere EU/UK/EEA data subjects are involved, where even business contact data can be personal data). Establish a lawful basis before you send anything cold, identify yourself honestly, and honour opt-out and unsubscribe requests promptly and permanently.
* **Do not lower the delays.** The default `--delay` between place pages and the fixed pause between queries are deliberately conservative. They exist so this tool behaves like a considerate client rather than a denial-of-service source. Turning them down makes blocks more likely, and it pushes your cost onto someone else's infrastructure.
* **Do not resell harvested lists.** This tool is for building your own prospect list for your own outreach. Selling, renting, or redistributing scraped contact data is a separate and considerably riskier activity, and it is not what this project is for.
* **No warranty.** This software is provided as-is, without warranty of any kind, express or implied. Selectors break when Google changes its markup, results are incomplete by nature, and email matches from DuckDuckGo are best-effort guesses that can be wrong. Verify anything you act on. See the [LICENSE](LICENSE) for the full disclaimer.

Nothing here is legal advice. If you are running outreach at any real scale, talk to a lawyer who knows your jurisdiction.

---

## 🛠️ Troubleshooting & FAQs

### Q: Why do I see `HTTP Error 403: Forbidden` during email lookup?
* **A**: DuckDuckGo has temporarily flagged your IP address for high-volume automated searching. The scraper is built to handle this gracefully: it logs the error, sets the `Email` column to `N/A`, and **continues crawling** phone numbers and addresses without stopping.

### Q: Playwright fails with "Executable doesn't exist"?
* **A**: You missed installing the browser binaries. Run the following command inside your active virtual environment to download Chromium:
  ```bash
  playwright install chromium
  ```

### Q: Can I run this script on a recurring cron job?
* **A**: Yes. Ensure your cron script activates the virtual environment first:
  ```bash
  #!/bin/bash
  cd /path/to/google-maps-scraper
  source venv/bin/activate
  python scraper.py --industry "construction" --state NJ --max-results 5
  ```

---

## 📄 License

Released under the **MIT License**. See the [LICENSE](LICENSE) file for the full text, including the no-warranty and no-liability disclaimer.

Copyright (c) 2026 Robby J ([github.com/Robj1925](https://github.com/Robj1925)).

The bundled county database is third-party data. See [Data Sources & Attribution](#-data-sources--attribution).
