# 🤖 AI Agent Integration Guide (`AGENT.md`)

This guide is a technical instruction manual designed for AI Coding Assistants, Developer Agents (such as Antigravity, Claude, or GPT-based executors), and automated workflow schedulers looking to orchestrate, execute, or extend the Google Maps Lead Scraper.

---

## 📖 Table of Contents
1. [Agent Execution Protocol](#-agent-execution-protocol)
2. [CLI Recipe Table for Common Intents](#-cli-recipe-table-for-common-intents)
3. [Playbook: Running a Campaign Step-by-Step](#-playbook-running-a-campaign-step-by-step)
4. [Programmatic Processing of Scraped Data](#-programmatic-processing-of-scraped-data)
5. [Error Handling & Anti-Bot Failures](#-error-handling--anti-bot-failures)

---

## 🧭 Agent Execution Protocol

When an AI Agent is tasked with running a lead generation campaign, it **must** execute according to the following protocol to maintain system stability and prevent target service blocking:

```
         [Step 1: Check Dependencies]
                       │
                       ▼
         [Step 2: Check Local Database]
                       │
                       ▼
        [Step 3: Spawn Background Scrape]
                       │
                       ▼
        [Step 4: Monitor Log & CSV size]
                       │
                       ▼
         [Step 5: Load and Deliver CSV]
```

* **Step 1: Check Dependencies**: Verify the virtual environment is active and that `playwright` and `pandas` are installed, plus the Chromium binary (`playwright install chromium`). The scraper needs **no API keys and no `.env` file**: it reads no environment variables at all.
* **Step 2: Check Local Database**: Check if `counties_by_state.json` exists in the script directory. If missing, explain to the user that the first campaign run will fetch the ~700KB database dynamically (self-healing mechanism).
* **Step 3: Spawn Background Scrape**: Always launch `scraper.py` using a background task manager or shell runner with `PAGER=cat`.
* **Step 4: Monitor Log & CSV Size**: Periodically check the number of rows inside the output CSV to report real-time incremental progress to the user.
* **Step 5: Load and Deliver CSV**: Parse the final deduplicated CSV results using standard libraries (`pandas` or `csv`) and display them in a clean markdown table.

---

## 🛠️ CLI Recipe Table for Common Intents

AI Agents must translate user requests into precise CLI calls. Use this reference mapping:

| User Request | Translated Agent Shell Command |
| :--- | :--- |
| *“Find roofing leads in New Jersey”* | `python scraper.py --industry "roofing" --state NJ` |
| *“Scrape construction companies in Texas”* | `python scraper.py --industry "construction" --state TX` |
| *“Scrape hair salons in Brooklyn and Queens”* | `python scraper.py --industry "hair salon" --counties "Kings County NY, Queens County NY"` |
| *“Find a plumber in Salem, NY right now”* | `python scraper.py --query "plumbing in Salem, NY" --max-results 3` |
| *“Run a fast test for electricians”* | `python scraper.py --query "electrician in Milltown, NJ" --max-results 1 --csv "test_run.csv"` |
| *“Scrape landscaping leads in NY up to 5 results per county”* | `python scraper.py --industry "landscaping" --state NY --max-results 5` |

---

## 📖 Playbook: Running a Campaign Step-by-Step

Here is the exact terminal execution workflow an agent must run to launch a dynamic lead campaign:

### 1. Verification of Dependencies
Before launching, confirm the virtual environment is utilized:
```bash
# On macOS/Linux:
source venv/bin/activate
```

### 2. Launching the Scraper
Run the script with the desired state or region, piping stdout/stderr into a log for background progress checks:
```bash
python scraper.py --industry "construction" --state NJ --max-results 5 --csv "leads.csv" > run.log 2>&1 &
```

### 3. Monitoring Progress
Read the log file or count the rows incrementally inside `leads.csv`:
```bash
# Count total accumulated leads
wc -l leads.csv

# Tail the active progress logs
tail -n 15 run.log
```

---

## 📊 Programmatic Processing of Scraped Data

After the scraper concludes, the agent should parse the resulting CSV dynamically.

### Python Ingestion Recipe
```python
import pandas as pd
import json

# Ingest leads sheet
df = pd.read_csv("leads.csv")

# Filter out rows that lack phone numbers (unactionable)
actionable_leads = df[df["Phone"] != "N/A"]

# Group by county or region (optional)
actionable_leads["County"] = actionable_leads["Address"].apply(
    lambda addr: addr.split(",")[-2].strip() if pd.notna(addr) and len(addr.split(",")) > 2 else "Unknown"
)

# Convert to list of dicts for pipeline processing
leads_list = actionable_leads.to_dict(orient="records")
print(f"Loaded {len(leads_list)} actionable leads for outreach.")
```

---

## ⚠️ Error Handling & Anti-Bot Failures

AI Agents must handle network exceptions and rate limits cleanly without crashing or blocking downstream tasks:

### 1. `HTTP Error 403: Forbidden` (DuckDuckGo Email Search)
* **What it means**: DuckDuckGo flagged the machine's IP for bot behavior.
* **Agent Handling**: Do **not** terminate execution. The script catches this error automatically, writes `Email: N/A` to the sheet, and proceeds to extract the name, phone number, and address from Google Maps. Explain to the user that phone outreach is still fully active!

### 2. `Timeout 15000ms exceeded` (Playwright Feed Selector)
* **What it means**: Google Maps search did not load its listings feed in time.
* **Agent Handling**: Check the system internet connection. The script will throw an exception, save the progress incrementally, and exit safely. The agent can resume the run by calling the command again (it will auto-deduplicate existing rows).

### 3. `playwright.io.Error: Browser closed`
* **What it means**: Headless Chromium crashed or browser binaries are corrupt.
* **Agent Handling**: Execute the browser installer dynamically:
  ```bash
  ./venv/bin/playwright install chromium
  ```
  Then re-launch the scraper.
