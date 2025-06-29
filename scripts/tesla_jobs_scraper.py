from playwright.sync_api import sync_playwright
import json
import os
import time

def process_jobs_data(json_data, output_file="../jobs/tesla_jobs_processed.json"):
    """Process the raw Tesla jobs JSON data and save as structured JSON file, sorted by job ID in descending order."""
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    # Extract the job listings
    listings = json_data.get("listings", [])
    print(f"Found {len(listings)} job listings.")
    
    # Create dictionaries to map IDs to human-readable names
    locations = {}
    for loc_id, loc_name in json_data.get("lookup", {}).get("locations", {}).items():
        locations[loc_id] = loc_name
        
    departments = {}
    for dept_id, dept_name in json_data.get("lookup", {}).get("departments", {}).items():
        departments[dept_id] = dept_name
    
    # Process the data
    job_data = []
    for job in listings:
        # Extract job details
        job_id = job.get("id", "")
        title = job.get("t", "")
        department_id = job.get("dp", "")
        location_id = job.get("l", "")
        
        # Map IDs to human-readable names
        department = departments.get(department_id, "Unknown Department")
        location = locations.get(location_id, "Unknown Location")
        
        # Create job entry
        # Create slug from title for URL (lowercase, replace spaces with hyphens, remove special chars)
        slug = title.lower()
        # Remove quotes and special characters
        slug = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in slug)
        # Replace spaces with hyphens and remove multiple consecutive hyphens
        slug = '-'.join(filter(None, slug.split()))
        
        job_entry = {
            "Job ID": job_id,
            "Title": title,
            "Department": department,
            "Location": location,
            "Job URL": f"https://www.tesla.com/careers/search/job/{slug}-{job_id}"
        }
        
        # Add all other fields that might be useful
        for key, value in job.items():
            if key not in ["id", "t", "dp", "l"]:
                job_entry[key] = value
                
        job_data.append(job_entry)

    # Process the JSON data
    if job_data:
        # Sort job_data by Job ID in descending order (most recent first)
        job_data_sorted = sorted(job_data, key=lambda x: int(x.get("Job ID", 0)), reverse=True)
        
        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(job_data_sorted, json_file, indent=2)
        
        print(f"Successfully processed {len(job_data)} jobs to JSON: {output_file}")
        
        # Check for update date information in the JSON
        print("\nChecking for job update date information:")
        
        # Check all job entries for date-related fields
        all_fields = set()
        for job in job_data:
            all_fields.update(job.keys())
        
        date_fields = [field for field in all_fields if any(keyword in field.lower() for keyword in ["date", "updated", "timestamp"])]
        
        if date_fields:
            print(f"Found potential update date fields: {', '.join(date_fields)}")
        else:
            print("No explicit update date fields found in the job data.")
            
            # Check for any other metadata at the top level that might indicate timing
            top_level_time_fields = []
            for key in json_data.keys():
                if any(keyword in key.lower() for keyword in ["date", "updated", "timestamp", "time"]):
                    top_level_time_fields.append(key)
            
            if top_level_time_fields:
                print(f"Found potential time-related fields at the top level: {', '.join(top_level_time_fields)}")
            else:
                print("No time-related fields found at the top level of the JSON.")
                
        return job_data_sorted
    else:
        print("No job data found.")
        return []


def main():
    raw_json_file = "../jobs/tesla_jobs_playwright.json"
    processed_json_file = "../jobs/tesla_jobs_processed.json"
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(raw_json_file), exist_ok=True)
    
    print(f"=== Tesla Jobs Scraper ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    with sync_playwright() as p:
        print("Launching browser...")
        # Always use non-headless mode as headless may prevent certain APIs/cookies from loading
        # Check if we're in GitHub Actions environment
        in_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
        
        # Setup browser arguments with specific optimizations for different environments
        browser_args = [
            '--disable-dev-shm-usage',  # Overcome limited /dev/shm size in CI
            '--no-sandbox',             # Required for running as root in container
            '--disable-setuid-sandbox',  # Additional sandbox security bypass for CI
            '--disable-gpu'             # Helps with headless rendering issues
        ]
        
        # Add additional arguments for GitHub Actions environment
        if in_github_actions:
            print("[*] Running in GitHub Actions environment - using non-headless mode with special CI configuration")
            browser_args.extend([
                '--disable-web-security',  # Bypass CORS for API requests
                '--disable-features=IsolateOrigins,site-per-process',  # Improve stability in CI
                '--disable-site-isolation-trials',
                '--mute-audio',  # Prevent audio issues in CI
                '--window-size=1920,1080'  # Explicitly set window size
            ])
        else:
            print("[*] Running in local environment")
        
        # User agent that mimics a real browser for better API compatibility
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        
        # Launch browser in non-headless mode with consistent viewport
        browser = p.chromium.launch(headless=False, args=browser_args)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent
        )
            
        json_data = None

        # Open a new page
        page = context.new_page()

        # Track all API responses for debugging
        all_api_responses = []
        
        # Function to capture the API response
        def handle_response(response):
            nonlocal json_data, all_api_responses
            
            # Log all API responses for debugging
            if response.url.startswith('http') and 'api' in response.url.lower():
                all_api_responses.append({
                    'url': response.url,
                    'status': response.status,
                    'type': response.request.resource_type
                })
            
            # Look for Tesla careers API response
            if ("cua-api/apps/careers/state" in response.url or "careers" in response.url) and response.status == 200:
                print(f"[+] Intercepted potential API response: {response.url} (Status: {response.status})")
                try:
                    response_json = response.json()
                    
                    # Check if this response has job listings
                    has_listings = isinstance(response_json, dict) and "listings" in response_json
                    
                    if has_listings:
                        json_data = response_json
                        print(f"[+] Found job listings in response from: {response.url}")
                        print("=== Top-level keys ===")
                        for key in json_data.keys():
                            print(f"  {key}")
                            
                        # Save the full JSON
                        with open(raw_json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2)
                        print(f"\nSaved {raw_json_file}!")
                    else:
                        print(f"[-] Response doesn't contain job listings from: {response.url}")
                        # Print a sample of the response for debugging (first ~100 chars)
                        sample = str(response_json)[:100] + "..." if len(str(response_json)) > 100 else str(response_json)
                        print(f"Sample response: {sample}")
                except Exception as e:
                    print(f"Failed to parse JSON from {response.url}: {e}")

        # Add listener BEFORE navigation
        page.on("response", handle_response)

        print("[*] Navigating to Tesla careers page...")
        page.wait_for_timeout(2000)  # Wait 2 seconds before navigation
        
        try:
            # Increase timeout and add more robust error handling
            print("[*] Loading Tesla careers page...")
            response = page.goto("https://www.tesla.com/careers/search/?type=3&site=US", timeout=90000)
            if not response or response.status >= 400:
                print(f"[!] Page navigation failed or returned status: {response.status if response else 'unknown'}")
                
            # Wait for the page to be fully loaded
            page.wait_for_load_state("networkidle", timeout=30000)
            print("[*] Page loaded, waiting for content to stabilize...")
            
            # Try to find the job listings container to ensure the page is properly loaded
            try:
                # Wait for any element that indicates the job listings have loaded
                page.wait_for_selector('.job-listings, .listings-container, .results-container', timeout=30000)
                print("[+] Job listings container detected")
            except Exception as e:
                print(f"[!] Could not find job listings container: {e}")
                # Continue anyway, as the API request might still have happened
            
            # Give page more time to load + make API calls
            print("[*] Waiting for API calls to complete...")
            page.wait_for_timeout(20000)  # Wait 20 seconds for requests to finish
            
            # Try scrolling to trigger any lazy-loading or additional API calls
            print("[*] Scrolling to trigger additional content...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            page.wait_for_timeout(5000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"[!] Error during page navigation and loading: {e}")

        # Print summary of all API responses for debugging before closing browser
        print("\n[*] API Response Summary:")
        if all_api_responses:
            print(f"Total API responses captured: {len(all_api_responses)}")
            for idx, resp in enumerate(all_api_responses[:10]):  # Show first 10 responses only
                print(f"  {idx+1}. {resp['url']} - Status: {resp['status']} - Type: {resp['type']}")
            
            if len(all_api_responses) > 10:
                print(f"  ... and {len(all_api_responses) - 10} more responses")
                
            # Check specifically for Tesla careers API
            tesla_careers_apis = [r for r in all_api_responses if "careers" in r["url"] or "cua-api" in r["url"]]
            if tesla_careers_apis:
                print(f"\n[+] Found {len(tesla_careers_apis)} Tesla careers-related API responses:")
                for idx, resp in enumerate(tesla_careers_apis):
                    print(f"  {idx+1}. {resp['url']} - Status: {resp['status']}")
            else:
                print("\n[-] No Tesla careers API responses were detected! This is likely the issue.")
        else:
            print("No API responses were captured during browsing!")
        
        # Take screenshot before closing the browser (helpful for debugging)
        try:
            screenshots_dir = "../jobs/debug_screenshots"
            os.makedirs(screenshots_dir, exist_ok=True)
            screenshot_path = f"{screenshots_dir}/tesla_careers_page_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            print(f"[*] Saved screenshot to {screenshot_path}")
        except Exception as e:
            print(f"[!] Failed to take screenshot: {e}")

        # Close the browser
        browser.close()
        print("Browser closed.")
        
        # Process JSON if data was captured
        if json_data:
            print("\n[*] Processing job data to JSON...")
            process_jobs_data(json_data, processed_json_file)
            
            # In GitHub Actions, keep the raw file for debugging purposes
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                print(f"[*] Running in GitHub Actions - keeping raw JSON file for debugging")
            else:
                # Delete the raw JSON file after processing (only in local environment)
                if os.path.exists(raw_json_file):
                    try:
                        os.remove(raw_json_file)
                        print(f"[*] Deleted raw JSON file: {raw_json_file}")
                    except Exception as e:
                        print(f"Warning: Could not delete raw JSON file: {e}")
            
            print(f"\n✅ Process complete! Check {processed_json_file} for the sorted job listings.")
        else:
            # Try to load from file if API response wasn't captured
            if os.path.exists(raw_json_file):
                print(f"\n[*] Loading job data from existing {raw_json_file}...")
                with open(raw_json_file, "r", encoding="utf-8") as f:
                    try:
                        json_data = json.load(f)
                        process_jobs_data(json_data, processed_json_file)
                        
                        # In GitHub Actions, keep the raw file for debugging
                        if os.environ.get('GITHUB_ACTIONS') != 'true':
                            # Delete the raw JSON file after processing
                            try:
                                os.remove(raw_json_file)
                                print(f"[*] Deleted raw JSON file: {raw_json_file}")
                            except Exception as e:
                                print(f"Warning: Could not delete raw JSON file: {e}")
                        
                        print(f"\n✅ Process complete! Check {processed_json_file} for the sorted job listings.")
                    except Exception as e:
                        print(f"Error loading JSON from file: {e}")
            else:
                # Print diagnostic message and environment variables
                print(f"\n[*] No job data captured and no existing {raw_json_file} file found.")
                
                # Print GitHub Actions environment variables for debugging if running in CI
                if os.environ.get('GITHUB_ACTIONS') == 'true':
                    print("\n[*] GitHub Actions Environment Variables:")
                    for key in sorted(os.environ.keys()):
                        if key.startswith('GITHUB_'):
                            print(f"  {key}={os.environ[key]}")
                            
                print(f"❌ No job data captured. No Tesla jobs will be updated.")


if __name__ == "__main__":
    main()
