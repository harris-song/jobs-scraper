from playwright.sync_api import sync_playwright
import json
import os
import time
from date_utils import add_scrape_metadata

def process_jobs_data(json_data, output_file):
    """Process the raw Salesforce jobs JSON data and save as structured JSON file."""
    # Ensure the jobs directory exists
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    job_postings = json_data.get("jobPostings", [])
    print(f"Found {len(job_postings)} job postings.")

    job_data = []
    for job in job_postings:
        external_path = job.get("externalPath", "")
        job_id = external_path.split("_")[-1] if external_path else ""
        title = job.get("title", "")
        location = job.get("locationsText", "")
        posted_date = job.get("postedOn", "")
        bullet_fields = job.get("bulletFields", [])
        job_entry = {
            "Job ID": job_id,
            "Title": title,
            "Location": location,
            "Posted Date": posted_date,
            "Job URL": f"https://salesforce.wd12.myworkdayjobs.com/External_Career_Site{external_path}",
            "External Path": external_path,
            "Bullet Fields": bullet_fields,
            "Requisition ID": bullet_fields[0] if bullet_fields else "",
        }
        
        # Add other fields
        for key, value in job.items():
            if key not in ["externalPath", "title", "locationsText", "postedOn", "bulletFields"]:
                job_entry[key] = value
        
        # Standardize date format and add scrape metadata
        job_entry = add_scrape_metadata(job_entry)
        job_data.append(job_entry)

    if job_data:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(job_data, json_file, indent=2, ensure_ascii=False)
        print(f"Successfully processed {len(job_data)} jobs to JSON: {output_file}")
    else:
        print("No job data found.")
    return job_data

def main():
    raw_json_file = "../jobs/salesforce_jobs_playwright.json"
    processed_json_file = "../jobs/salesforce_jobs_processed.json"
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(raw_json_file), exist_ok=True)

    print(f"=== Salesforce Jobs Scraper (Playwright) ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        all_jobs = []
        page = context.new_page()

        def handle_response(response):
            nonlocal all_jobs
            if "/wday/cxs/salesforce/External_Career_Site/jobs" in response.url and response.status == 200:
                print(f"[+] Intercepted API response: {response.url}")
                try:
                    json_data = response.json()
                    job_postings = json_data.get("jobPostings", [])
                    print(f"Found {len(job_postings)} jobs in this batch")
                    all_jobs.extend(job_postings)
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")

        page.on("response", handle_response)

        print("[*] Navigating to Salesforce careers page...")
        page.goto("https://salesforce.wd12.myworkdayjobs.com/External_Career_Site", timeout=60000)
        print("[*] Waiting for initial API calls to complete...")
        page.wait_for_timeout(10000)  # Wait 10 seconds for requests to finish
        
        # Try to load more jobs by scrolling and clicking "Load More" if available
        max_iterations = 10  # Limit to prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            print(f"[*] Attempting to load more jobs (iteration {iteration + 1})...")
            
            # Scroll to bottom to trigger any lazy loading
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            
            # Look for "Load More" or "Show More" buttons
            load_more_selectors = [
                "button[data-automation-id='loadMoreJobs']",
                "button:has-text('Load More')",
                "button:has-text('Show More')",
                "button:has-text('See More')",
                "[data-automation-id='paginationMoreButton']",
                ".css-19uc56f",  # Common Workday pagination button class
                "button[aria-label*='more']"
            ]
            
            button_found = False
            for selector in load_more_selectors:
                try:
                    load_more_button = page.locator(selector).first
                    if load_more_button.is_visible(timeout=2000):
                        print(f"[+] Found load more button with selector: {selector}")
                        load_more_button.click()
                        page.wait_for_timeout(5000)  # Wait for new jobs to load
                        button_found = True
                        break
                except:
                    continue
            
            if not button_found:
                print("[*] No more load buttons found, trying pagination...")
                # Try pagination
                try:
                    next_button = page.locator("button[aria-label='Go to next page']").first
                    if next_button.is_visible(timeout=2000):
                        print("[+] Found next page button")
                        next_button.click()
                        page.wait_for_timeout(5000)
                    else:
                        print("[*] No pagination found, stopping...")
                        break
                except:
                    print("[*] No more pages available, stopping...")
                    break
            
            iteration += 1
        
        browser.close()
        print("Browser closed.")
        
        # Combine all collected jobs
        if all_jobs:
            combined_data = {"jobPostings": all_jobs}
            with open(raw_json_file, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=2)
            print(f"[+] Collected total of {len(all_jobs)} jobs across all pages")            
            print("\n[*] Processing job data to JSON...")
            process_jobs_data(combined_data, processed_json_file)
            if os.path.exists(raw_json_file):
                try:
                    os.remove(raw_json_file)
                    print(f"[*] Deleted raw JSON file: {raw_json_file}")
                except Exception as e:
                    print(f"Warning: Could not delete raw JSON file: {e}")
            print(f"\n✅ Process complete! Check {processed_json_file} for the job listings.")
        else:
            if os.path.exists(raw_json_file):
                print(f"\n[*] Loading job data from existing {raw_json_file}...")
                with open(raw_json_file, "r", encoding="utf-8") as f:
                    try:
                        json_data = json.load(f)
                        process_jobs_data(json_data, processed_json_file)
                        try:
                            os.remove(raw_json_file)
                            print(f"[*] Deleted raw JSON file: {raw_json_file}")
                        except Exception as e:
                            print(f"Warning: Could not delete raw JSON file: {e}")
                        print(f"\n✅ Process complete! Check {processed_json_file} for the job listings.")
                    except Exception as e:
                        print(f"Error loading JSON from file: {e}")
            else:
                print(f"❌ No job data captured and no existing {raw_json_file} file found.")

if __name__ == "__main__":
    main() 