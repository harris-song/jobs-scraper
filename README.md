# Jobs Scraper & Dashboard

A comprehensive job scraping tool that automatically collects job listings from major tech companies and saves them as structured JSON data, with a web dashboard to browse the listings.

## 🚀 Quick Start

1. Clone this repository
2. Open `index.html` in your web browser to view the jobs dashboard
3. For automated scraping, set up the GitHub Action workflow

## 🏢 Supported Companies

- **Apple** - Apple Careers
- **Meta** - Meta Careers  
- **NVIDIA** - NVIDIA Careers
- **Salesforce** - Salesforce Careers
- **Accenture** - Accenture Careers
- **Tesla** - Tesla Careers

## �️ Jobs Dashboard

The project includes a web-based dashboard to browse all scraped job listings:

### Features
- **Responsive Design**: Works on desktop and mobile devices
- **Filtering**: Filter jobs by company and location
- **Search**: Search across all job listings by keyword
- **Pagination**: Easily navigate through large numbers of job listings
- **Direct Links**: Apply directly by clicking through to the original job posting

### How to Use
1. Open `index.html` in your web browser
2. Use the search box to find specific jobs
3. Filter by company or location using the dropdown menus
4. Click "View Job" to open the original job posting in a new tab

## �📁 Project Structure

```
jobs-scraper/
├── .github/workflows/
│   └── job-scraper.yml          # GitHub Actions automation
├── jobs/                        # Output directory for job data
│   ├── apple_jobs_processed.json
│   ├── meta_jobs_processed.json
│   ├── nvidia_jobs_processed.json
│   ├── salesforce_jobs_processed.json
│   ├── tesla_jobs_processed.json
│   └── accenture_jobs_processed.json
├── scripts/                     # Alternative script versions
│   ├── apple_jobs_scraper.py        # Apple jobs scraper
│   ├── meta_jobs_scraper.py         # Meta jobs scraper
│   ├── nvidia_jobs_scraper.py       # NVIDIA jobs scraper
│   ├── salesforce_jobs_scraper.py   # Salesforce jobs scraper
│   ├── tesla_jobs_scraper.py        # Tesla jobs scraper
│   ├── accenture_jobs_scraper.py    # Accenture jobs scraper
├── index.html                   # Jobs dashboard main page
├── app.js                       # Dashboard JavaScript functionality
├── styles.css                   # Dashboard styling
├── images/                      # Images for the dashboard
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🤖 GitHub Actions Automation

This project includes automated job scraping using GitHub Actions:

### Features
- **Daily Automation**: Runs every day at 6 AM UTC
- **Manual Trigger**: Can be triggered manually via GitHub Actions
- **Auto-commit**: Automatically commits updated job data
- **Artifact Storage**: Stores job data as downloadable artifacts
- **Summary Reports**: Generates detailed reports with job counts
- **Error Handling**: Continues running even if individual scrapers fail

### Workflow Triggers
- **Scheduled**: Daily at 6 AM UTC (`0 6 * * *`)
- **Manual**: Via GitHub Actions UI
- **Push**: When code is pushed to main branch

### What the Workflow Does
1. **Setup**: Installs Python and dependencies
2. **Scraping**: Runs all job scrapers in parallel
3. **Processing**: Saves job data as JSON files
4. **Commit**: Automatically commits changes if new data is found
5. **Artifacts**: Uploads job data as downloadable artifacts
6. **Summary**: Generates a detailed report with job counts

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/bobbykabob/jobs-scraper.git
cd jobs-scraper

# Install dependencies
pip install -r requirements.txt
```

### Running Individual Scrapers
```bash
# Run Apple jobs scraper
python apple_jobs_scraper.py

# Run Meta jobs scraper
python meta_jobs_scraper.py

# Run NVIDIA jobs scraper
python nvidia_jobs_scraper.py

# Run Salesforce jobs scraper
python salesforce_jobs_scraper.py

# Run Tesla jobs scraper
python tesla_jobs_scraper.py

# Run Accenture jobs scraper
python accenture_jobs_scraper.py
```

### Running All Scrapers
```bash
# Run all scrapers
for scraper in *_jobs_scraper.py; do
    echo "Running $scraper..."
    python "$scraper"
done
```

## 📊 Data Format

Each scraper generates a JSON file with the following structure:

```json
[
  {
    "Job ID": "200598711",
    "Title": "Software Engineer",
    "Location": "Cupertino, CA",
    "Posted Date": "Jun 29, 2025",
    "Job URL": "https://jobs.company.com/details/200598711",
    "Team": "Engineering",
    "Weekly Hours": "40 Hours",
    "Summary": "Job description...",
    "Company": "Company Name"
  }
]
```

## 🔧 Configuration

### Customizing Scraping Schedule
Edit `.github/workflows/job-scraper.yml` to change the cron schedule:

```yaml
schedule:
  # Run every day at 6 AM UTC
  - cron: '0 6 * * *'
  
  # Run every Monday at 9 AM UTC
  # - cron: '0 9 * * 1'
  
  # Run every hour
  # - cron: '0 * * * *'
```

### Adding New Companies
1. Create a new scraper file (e.g., `google_jobs_scraper.py`)
2. Add the scraper to the GitHub Actions workflow
3. Follow the existing data format structure

## 📈 Monitoring

### GitHub Actions Dashboard
- View workflow runs: `https://github.com/bobbykabob/jobs-scraper/actions`
- Check job counts in the summary reports
- Download job data artifacts

### Job Data Tracking
- All job data is stored in the `jobs/` directory
- Files are automatically updated daily
- Historical data is preserved in git history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Test locally
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please respect the terms of service of the websites being scraped and ensure compliance with their robots.txt files and usage policies. 