import subprocess
import json
import csv
import os
import time
from datetime import datetime
import sys
import pathlib

# Add parent directory to path so we can execute this script from any directory
sys.path.append(str(pathlib.Path(__file__).parent.parent))

def fetch_jobs_with_curl(limit=20, offset=0):
    """Use curl via subprocess to fetch jobs from Accenture's Workday API."""
    url = "https://accenture.wd103.myworkdayjobs.com/wday/cxs/accenture/AccentureCareers/jobs"
    payload = json.dumps({
        "appliedFacets": {},
        "limit": limit,
        "offset": offset,
        "searchText": ""
    })
    curl_cmd = [
        "curl", "-s", "-X", "POST", url,
        "-H", "accept: application/json",
        "-H", "content-type: application/json",
        "-H", "origin: https://accenture.wd103.myworkdayjobs.com",
        "-H", "referer: https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers",
        "-H", "user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "-d", payload
    ]
    try:
        print(f"[*] Running curl for offset {offset}...")
        result = subprocess.run(curl_cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[!] Curl request failed: {e}")
        return None

def extract_job_id_from_path(external_path):
    if not external_path:
        return ""
    parts = external_path.split('/')
    if len(parts) > 0:
        last_part = parts[-1]
        if '_R' in last_part:
            return last_part.split('_R')[-1]
        elif 'R' in last_part:
            return last_part.split('R')[-1]
    return external_path

def process_jobs_data(json_data, output_file="../jobs/accenture_jobs_processed.json"):
    if not json_data:
        print("No JSON data to process.")
        return
    
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    print(f"=== Processing Accenture Jobs Data ===")
    print(f"Total jobs available: {json_data.get('total', 0)}")
    print(f"Jobs in this response: {len(json_data.get('jobPostings', []))}")
    job_postings = json_data.get("jobPostings", [])
    if not job_postings:
        print("No job postings found.")
        return
    job_data = []
    for job in job_postings:
        external_path = job.get("externalPath", "")
        job_id = extract_job_id_from_path(external_path)
        title = job.get("title", "")
        location = job.get("locationsText", "")
        posted_date = job.get("postedOn", "")
        bullet_fields = job.get("bulletFields", [])
        job_entry = {
            "Job ID": job_id,
            "Title": title,
            "Location": location,
            "Posted Date": posted_date,
            "Job URL": f"https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers{external_path}",
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
        # Save and then delete the raw API response
        raw_file_path = "../jobs/accenture_jobs_raw.json"
        # Ensure the jobs directory exists
        os.makedirs(os.path.dirname(raw_file_path), exist_ok=True)
        with open(raw_file_path, "w", encoding="utf-8") as raw_file:
            json.dump(json_data, raw_file, indent=2, ensure_ascii=False)
        print(f"Saved raw API response to: {raw_file_path}")
        # Delete the raw file after saving
        try:
            os.remove(raw_file_path)
            print(f"Deleted raw API response: {raw_file_path}")
        except Exception as e:
            print(f"[!] Could not delete raw file: {e}")
    else:
        print("No job data found.")

def main():
    print(f"=== Accenture Jobs Scraper (curl) ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    json_data = fetch_jobs_with_curl(limit=20, offset=0)
    if json_data:
        process_jobs_data(json_data, "../jobs/accenture_jobs_processed.json")
        print("\n✅ Process complete!")
        print("📄 JSON file: ../jobs/accenture_jobs_processed.json")
    else:
        print("❌ Failed to retrieve job data from Accenture API.")

if __name__ == "__main__":
    main()
