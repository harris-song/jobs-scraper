from playwright.sync_api import sync_playwright
import json
import os
import time
from date_utils import add_scrape_metadata

def extract_job_id_from_path(external_path):
    """Extract the job ID from the external path."""
    if not external_path:
        return ""
    
    # Extract the job ID from the end of the path
    parts = external_path.split('/')
    if len(parts) > 0:
        last_part = parts[-1]
        # Remove the job title part and keep just the ID
        if '_JR' in last_part:
            return last_part.split('_JR')[-1]
        elif 'JR' in last_part:
            return last_part.split('JR')[-1]
    
    return external_path

def load_existing_jobs(output_file):
    """Load existing jobs from the JSON file if it exists."""
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_jobs = json.load(f)
                print(f"Loaded {len(existing_jobs)} existing jobs from {output_file}")
                return existing_jobs
        except Exception as e:
            print(f"Warning: Could not load existing jobs file: {e}")
            return []
    else:
        print(f"No existing jobs file found at {output_file}")
        return []

def process_jobs_data(json_data, output_file="../jobs/nvidia_jobs_processed.json"):
    """Process the raw NVIDIA jobs JSON data and append new jobs to existing data."""
    # Ensure the jobs directory exists
    if output_file and output_file != "nvidia_jobs_processed.json":
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    elif output_file == "nvidia_jobs_processed.json":
        output_file = "../jobs/nvidia_jobs_processed.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Load existing jobs
    existing_jobs = load_existing_jobs(output_file)
    existing_job_ids = {job.get("Job ID", "") for job in existing_jobs if job.get("Job ID")}
    
    job_postings = json_data.get("jobPostings", [])
    print(f"Found {len(job_postings)} job postings from scrape.")
    
    new_jobs = []
    updated_jobs = []
    
    for job in job_postings:
        external_path = job.get("externalPath", "")
        job_id = extract_job_id_from_path(external_path)
        title = job.get("title", "")
        location = job.get("locationsText", "")
        posted_date = job.get("postedOn", "")
        bullet_fields = job.get("bulletFields", [])
        
        # Create job entry with comprehensive information
        job_entry = {
            "Job ID": job_id,
            "Title": title,
            "Location": location,
            "Posted Date": posted_date,
            "Job URL": f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{external_path}",
            "External Path": external_path,
            "Bullet Fields": bullet_fields,
            "Requisition ID": bullet_fields[0] if bullet_fields else ""
        }
        
        # Add all other fields that might be useful
        for key, value in job.items():
            if key not in ["externalPath", "title", "locationsText", "postedOn", "bulletFields"]:
                job_entry[key] = value
        
        # Standardize date format and add scrape metadata
        job_entry = add_scrape_metadata(job_entry)
        
        # Check if this is a new job or an update to existing job
        if job_id and job_id in existing_job_ids:
            # Job already exists, update it in the existing jobs list
            for i, existing_job in enumerate(existing_jobs):
                if existing_job.get("Job ID") == job_id:
                    # Update the existing job with new data
                    existing_jobs[i] = job_entry
                    updated_jobs.append(job_entry)
                    break
        else:
            # This is a new job
            new_jobs.append(job_entry)
    
    # Combine existing jobs with new jobs
    all_jobs = existing_jobs + new_jobs
    
    # Process the JSON data
    if all_jobs:
        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(all_jobs, json_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully processed jobs to JSON: {output_file}")
        print(f"  - Total jobs: {len(all_jobs)}")
        print(f"  - New jobs added: {len(new_jobs)}")
        print(f"  - Existing jobs updated: {len(updated_jobs)}")
        print(f"  - Existing jobs unchanged: {len(existing_jobs) - len(updated_jobs)}")
        
        if new_jobs:
            print(f"\nNew jobs added:")
            for job in new_jobs[:5]:  # Show first 5 new jobs
                print(f"  - {job.get('Title', 'Unknown Title')} (ID: {job.get('Job ID', 'Unknown')})")
            if len(new_jobs) > 5:
                print(f"  ... and {len(new_jobs) - 5} more")
                
    else:
        print("No job data found.")

def main():
    raw_json_file = "../jobs/nvidia_jobs_playwright.json"
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(raw_json_file), exist_ok=True)
    processed_json_file = "nvidia_jobs_processed.json"

    print(f"=== NVIDIA Jobs Scraper (Playwright) ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        json_data = None
        page = context.new_page()

        def handle_response(response):
            nonlocal json_data
            if "/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs" in response.url and response.status == 200:
                print(f"[+] Intercepted API response: {response.url}")
                try:
                    json_data = response.json()
                    with open(raw_json_file, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)
                    print(f"Saved {raw_json_file}!")
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")

        page.on("response", handle_response)

        print("[*] Navigating to NVIDIA careers page...")
        page.goto("https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite", timeout=60000)
        print("[*] Waiting for API calls to complete...")
        page.wait_for_timeout(10000)  # Wait 10 seconds for requests to finish
        browser.close()
        print("Browser closed.")

        if json_data:
            print("\n[*] Processing job data to JSON...")
            process_jobs_data(json_data, processed_json_file)
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