# BugLens — Website Health Scanner

A beginner-friendly MVP that scans a **public website you own or are authorized to test** for a small set of common quality issues.

## Features
- URL validation and bounded same-site crawl (maximum 20 pages; UI defaults to 10)
- HTTP response and fetch-error reporting
- Missing/empty page title detection
- Missing/empty meta description detection
- Images missing an `alt` attribute
- Evidence and suggested fixes for findings
- CSV export from the browser
- Responsive dashboard

## Requirements
- Python 3.10+
- Internet connection for scanning public websites

## Run locally

```bash
# 1. Open a terminal in the BugLens folder
python -m venv .venv

# 2. Activate the environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the app
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

API health check: http://127.0.0.1:8000/api/health

## Project structure

```text
BugLens/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── scanner.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── requirements.txt
└── README.md
```

## Important limitations and safe use
- Only scan websites you own or have permission to test.
- This is a first-pass quality checker, **not** a complete SEO, security, performance, or accessibility audit.
- It does not execute JavaScript, inspect authenticated pages, or guarantee every link was checked.
- Redirects are reported rather than followed, and fetch failures are not automatically treated as confirmed broken links.
- The app validates host addresses before requests and checks redirect destinations. For a public production service, add stronger DNS-rebinding-resistant networking, outbound firewall rules, per-user rate limits, request logging, abuse monitoring, and deployment-specific security review.
- Do not deploy this as an unrestricted public scanning service without those protections.
- Use fictional or non-sensitive data in demos. The scanner does not intentionally save scan results.

## Suggested learning exercises
1. Add tests for URL normalization and finding generation.
2. Add a dedicated link-checking queue with strict limits.
3. Add scan progress reporting.
4. Add a JSON export and saved scan history.
5. Improve the crawler's DNS and redirect protections before any public deployment.

## License
MIT (you may change this for your project).
