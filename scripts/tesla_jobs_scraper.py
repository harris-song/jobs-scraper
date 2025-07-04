from playwright.sync_api import sync_playwright
import json
import os
import time
from date_utils import add_scrape_metadata, get_current_utc_timestamp


def process_jobs_data(json_data, output_file):
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
            "Job URL": f"https://www.tesla.com/careers/search/job/{slug}-{job_id}",
            "Posted Date": ""  # Tesla doesn't provide posted dates in API
        }
        
        # Add all other fields that might be useful
        for key, value in job.items():
            if key not in ["id", "t", "dp", "l"]:
                job_entry[key] = value
        
        # Standardize date format and add scrape metadata
        job_entry = add_scrape_metadata(job_entry)
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
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_json_file = os.path.join(script_dir, "tesla_jobs_playwright.json")
    processed_json_file = os.path.join(script_dir, "../jobs/tesla_jobs_processed.json")
    
    print(f"=== Tesla Jobs Scraper ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        all_jobs_data = []
        all_locations = {}
        all_departments = {}

        # Open a new page
        page = context.new_page()

        # Function to capture the API response
        def handle_response(response):
            nonlocal all_jobs_data, all_locations, all_departments
            if "cua-api/apps/careers/state" in response.url and response.status == 200:
                print(f"[+] Intercepted API response: {response.url}")
                try:
                    json_data = response.json()
                    listings = json_data.get("listings", [])
                    print(f"Found {len(listings)} jobs in this batch")
                    all_jobs_data.extend(listings)
                    
                    # Collect lookup data
                    lookup = json_data.get("lookup", {})
                    if "locations" in lookup:
                        all_locations.update(lookup["locations"])
                    if "departments" in lookup:
                        all_departments.update(lookup["departments"])
                        
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")

        # Add listener BEFORE navigation
        page.on("response", handle_response)

        print("[*] Navigating to Tesla careers page...")
        page.wait_for_timeout(1000)  # Wait 1 second before navigation
        page.goto("https://www.tesla.com/careers/search/?type=3&site=US", timeout=60000)

        # Give page time to load + make API calls
        print("[*] Waiting for initial API calls to complete...")
        page.wait_for_timeout(10000)  # Wait 10 seconds for requests to finish
        
        # Try to load more jobs by scrolling and interacting with filters
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            print(f"[*] Attempting to load more jobs (iteration {iteration + 1})...")
            
            # Scroll to bottom to trigger any lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            
            # Try clicking different filters to load more job categories
            filter_selectors = [
                "button:has-text('All Locations')",
                "button:has-text('All Teams')",
                "button:has-text('Engineering')",
                "button:has-text('Manufacturing')", 
                "button:has-text('Sales & Service')",
                "button:has-text('Supply Chain')",
                "button:has-text('Information Technology')"
            ]
            
            # Try each filter to potentially load more jobs
            for selector in filter_selectors:
                try:
                    filter_button = page.locator(selector).first
                    if filter_button.is_visible(timeout=1000):
                        print(f"[+] Clicking filter: {selector}")
                        filter_button.click()
                        page.wait_for_timeout(3000)  # Wait for API calls
                        break
                except:
                    continue
            
            # Look for "Load More" or pagination buttons
            load_more_selectors = [
                "button:has-text('Load More')",
                "button:has-text('Show More')", 
                "button[data-testid='load-more']",
                ".load-more",
                "button[aria-label*='more']"
            ]
            
            button_found = False
            for selector in load_more_selectors:
                try:
                    load_more_button = page.locator(selector).first
                    if load_more_button.is_visible(timeout=2000):
                        print(f"[+] Found load more button: {selector}")
                        load_more_button.click()
                        page.wait_for_timeout(5000)
                        button_found = True
                        break
                except:
                    continue
            
            if not button_found:
                print("[*] No more load buttons found...")
            
            iteration += 1

        browser.close()
        print("Browser closed.")
        
        # Combine all collected data
        if all_jobs_data:
            combined_data = {
                "listings": all_jobs_data,
                "lookup": {
                    "locations": all_locations,
                    "departments": all_departments
                }
            }
            
            with open(raw_json_file, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2)
            print(f"[+] Collected total of {len(all_jobs_data)} jobs across all iterations")
            
            print("\n[*] Processing job data to JSON...")
            process_jobs_data(combined_data, processed_json_file)
            
            # Delete the raw JSON file after processing
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
                print(f"❌ No job data captured and no existing {raw_json_file} file found.")


if __name__ == "__main__":
    main()
