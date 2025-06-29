from playwright.sync_api import sync_playwright
import json
import os
import time

def process_jobs_data(json_data, output_file="jobs/salesforce_jobs_processed.json"):
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    """Process the raw Salesforce jobs JSON data and save as structured JSON file."""
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
        for key, value in job.items():
            if key not in ["externalPath", "title", "locationsText", "postedOn", "bulletFields"]:
                job_entry[key] = value
        job_data.append(job_entry)

    if job_data:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(job_data, json_file, indent=2, ensure_ascii=False)
        print(f"Successfully processed {len(job_data)} jobs to JSON: {output_file}")
    else:
        print("No job data found.")
    return job_data

def main():
    raw_json_file = "jobs/salesforce_jobs_playwright.json"
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(raw_json_file), exist_ok=True)
    processed_json_file = "salesforce_jobs_processed.json"

    print(f"=== Salesforce Jobs Scraper (Playwright) ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===")

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        json_data = None
        page = context.new_page()

        def handle_response(response):
            nonlocal json_data
            if "/wday/cxs/salesforce/External_Career_Site/jobs" in response.url and response.status == 200:
                print(f"[+] Intercepted API response: {response.url}")
                try:
                    json_data = response.json()
                    with open(raw_json_file, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)
                    print(f"Saved {raw_json_file}!")
                except Exception as e:
                    print(f"Failed to parse JSON: {e}")

        page.on("response", handle_response)

        print("[*] Navigating to Salesforce careers page...")
        page.goto("https://salesforce.wd12.myworkdayjobs.com/External_Career_Site", timeout=60000)
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