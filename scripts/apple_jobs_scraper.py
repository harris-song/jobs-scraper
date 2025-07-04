import requests
import json
import os
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import sys
import pathlib
from date_utils import add_scrape_metadata

# Add parent directory to path so we can execute this script from any directory
sys.path.append(str(pathlib.Path(__file__).parent.parent))

def fetch_jobs_with_requests(limit=20, offset=0, sort="newest"):
    """Fetch jobs from Apple's careers page using requests."""
    url = f"https://jobs.apple.com/en-us/search?sort={sort}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Sec-CH-UA": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"macOS"'
    }
    
    try:
        print(f"[*] Fetching Apple jobs page (sort: {sort})...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"[*] Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"[!] Error: {response.status_code}")
            print(f"[!] Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"[!] Request failed: {e}")
        return None

def extract_jobs_from_html(html_content):
    """Extract job data from the HTML content using BeautifulSoup."""
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []
    
    # Find all job list items
    job_items = soup.find_all('li', {'data-core-accordion-item': '', 'role': 'listitem'})
    
    print(f"[*] Found {len(job_items)} job items in HTML")
    
    for item in job_items:
        try:
            # Extract job title and link
            title_link = item.find('a', class_='link-inline')
            if not title_link:
                continue
                
            title = title_link.get_text(strip=True)
            job_url = "https://jobs.apple.com" + title_link.get('href', '')
            
            # Extract role number from the URL or nearby elements
            role_number = ""
            role_number_elem = item.find('span', id=re.compile(r'search-role-number.*'))
            if role_number_elem:
                role_number = role_number_elem.get_text(strip=True)
            else:
                # Try to extract from URL
                url_match = re.search(r'/details/(\d+)/', job_url)
                if url_match:
                    role_number = url_match.group(1)
            
            # Extract team name
            team_name = ""
            team_elem = item.find('span', class_='team-name')
            if team_elem:
                team_name = team_elem.get_text(strip=True)
            
            # Extract location
            location = ""
            location_elem = item.find('span', class_='table--advanced-search__location-sub')
            if location_elem:
                location = location_elem.get_text(strip=True)
            
            # Extract posted date
            posted_date = ""
            date_elem = item.find('span', class_='job-posted-date')
            if date_elem:
                posted_date = date_elem.get_text(strip=True)
            
            # Extract job summary
            job_summary = ""
            summary_elem = item.find('p', class_='text-align-start')
            if summary_elem:
                job_summary = summary_elem.get_text(strip=True)
            
            # Extract weekly hours
            weekly_hours = ""
            hours_elem = item.find('span', id=re.compile(r'search-weekly-hours.*'))
            if hours_elem:
                weekly_hours = hours_elem.get_text(strip=True)
            
            job_data = {
                "Job ID": role_number,
                "Title": title,
                "Location": location,
                "Posted Date": posted_date,
                "Job URL": job_url,
                "Team": team_name,
                "Weekly Hours": weekly_hours,
                "Summary": job_summary,
                "Company": "Apple"
            }
            
            # Standardize date format and add scrape metadata
            job_data = add_scrape_metadata(job_data)
            jobs.append(job_data)
            
        except Exception as e:
            print(f"[!] Error extracting job data: {e}")
            continue
    
    return jobs

def try_api_endpoints():
    """Try to find and test potential API endpoints."""
    potential_endpoints = [
        "https://jobs.apple.com/api/jobs",
        "https://jobs.apple.com/api/search",
        "https://jobs.apple.com/api/v1/jobs",
        "https://jobs.apple.com/api/v2/jobs",
        "https://jobs.apple.com/api/jobs/search",
        "https://jobs.apple.com/api/careers/jobs",
        "https://jobs.apple.com/api/positions",
        "https://jobs.apple.com/api/opportunities"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    for endpoint in potential_endpoints:
        try:
            print(f"[*] Testing API endpoint: {endpoint}")
            response = requests.get(endpoint, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"[+] Found working API endpoint: {endpoint}")
                try:
                    json_data = response.json()
                    print(f"[+] API response structure: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dict'}")
                    return endpoint, json_data
                except:
                    print(f"[+] API endpoint returns non-JSON data")
                    return endpoint, response.text
            else:
                print(f"[-] Endpoint {endpoint} returned status {response.status_code}")
                
        except Exception as e:
            print(f"[-] Endpoint {endpoint} failed: {e}")
    
    return None, None

def process_jobs_data(jobs_data, output_file="../jobs/apple_jobs_processed.json", raw_html_content=None):
    """Process the extracted jobs data and save as structured JSON file."""
    
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if not jobs_data:
        print("No jobs data to process.")
        return
    
    print(f"=== Processing Apple Jobs Data ===")
    print(f"Total jobs found: {len(jobs_data)}")
    
    if jobs_data:
        # Sort jobs by Posted Date (most recent first)
        def sort_key(job):
            posted = job.get("Posted Date", "")
            if "Today" in posted:
                return 0
            elif "Yesterday" in posted:
                return 1
            else:
                return 2
        
        jobs_sorted = sorted(jobs_data, key=sort_key)
        
        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(jobs_sorted, json_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully processed {len(jobs_sorted)} jobs to JSON: {output_file}")
        
        # Save raw HTML content for debugging if provided
        if raw_html_content:
            raw_file_path = "../jobs/apple_jobs_raw.html"
            # Ensure the jobs directory exists
            os.makedirs(os.path.dirname(raw_file_path), exist_ok=True)
            with open(raw_file_path, "w", encoding="utf-8") as html_file:
                html_file.write(raw_html_content)
            print(f"Saved raw HTML content to: {raw_file_path}")
            
            # Delete the raw file after saving
            try:
                os.remove(raw_file_path)
                print(f"Deleted raw HTML file: {raw_file_path}")
            except Exception as e:
                print(f"[!] Could not delete raw HTML file: {e}")
        
    else:
        print("No job data found.")

def main():
    print(f"=== Apple Jobs Scraper ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # First, try to find API endpoints
    print("\n[*] Searching for API endpoints...")
    api_endpoint, api_data = try_api_endpoints()
    
    if api_endpoint and api_data:
        print(f"\n[+] Found API endpoint: {api_endpoint}")
        # Process API data if found
        if isinstance(api_data, dict):
            process_jobs_data([api_data], "../jobs/apple_jobs_api_processed.json", api_data.get("html_content"))
        else:
            print(f"[!] API data is not in expected format")
    
    # Fallback to HTML scraping
    print("\n[*] Falling back to HTML scraping...")
    html_content = fetch_jobs_with_requests(limit=20, offset=0, sort="newest")
    
    if html_content:
        jobs_data = extract_jobs_from_html(html_content)
        process_jobs_data(jobs_data, "../jobs/apple_jobs_processed.json", html_content)
        print("\n✅ Process complete!")
        print("📄 JSON file: ../jobs/apple_jobs_processed.json")
    else:
        print("❌ Failed to retrieve job data from Apple careers page.")

if __name__ == "__main__":
    main()
