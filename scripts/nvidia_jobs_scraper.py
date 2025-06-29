import requests
import json
import csv
import os
import time
from datetime import datetime

def make_nvidia_api_request(limit=100, offset=0):
    """Make a direct POST request to NVIDIA's Workday API with proper headers and body."""
    
    url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
    
    # Updated headers for current API requirements
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://nvidia.wd5.myworkdayjobs.com",
        "Referer": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors",
        "sec-fetch-dest": "empty",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    # Updated request payload with required fields
    payload = {
        "appliedFacets": {},
        "limit": limit,
        "offset": offset,
        "searchText": "",
        "sortOrder": {
            "ascending": False,
            "sortBy": "postedOn"
        }
    }
    
    try:
        print(f"[*] Making POST request to NVIDIA API (limit: {limit}, offset: {offset})...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"[*] Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"[!] Error: {response.status_code}")
            print(f"[!] Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"[!] Request failed: {e}")
        return None

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

def process_jobs_data(json_data, output_file="../jobs/nvidia_jobs_processed.json"):
    """Process the raw NVIDIA jobs JSON data and save as structured JSON file."""
    
    # Ensure the jobs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Define raw JSON file path
    raw_json_file_path = "../jobs/nvidia_jobs_raw.json"
    
    if not json_data:
        print("No JSON data to process.")
        return
    
    print(f"=== Processing NVIDIA Jobs Data ===")
    print(f"Total jobs available: {json_data.get('total', 0)}")
    print(f"Jobs in this response: {len(json_data.get('jobPostings', []))}")
    
    # Extract job postings
    job_postings = json_data.get("jobPostings", [])
    
    if not job_postings:
        print("No job postings found.")
        return
    
    # Process the data
    job_data = []
    for job in job_postings:
        # Extract job details
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
            "Requisition ID": bullet_fields[0] if bullet_fields else "",
            "Department": "",  # Will be filled if available in detailed view
            "Job Type": "",    # Will be filled if available in detailed view
            "Experience Level": "",  # Will be filled if available in detailed view
            "Remote": "",      # Will be filled if available in detailed view
            "Description": "", # Will be filled if available in detailed view
            "Requirements": "", # Will be filled if available in detailed view
            "Benefits": "",    # Will be filled if available in detailed view
            "Salary Range": "", # Will be filled if available in detailed view
            "Work Schedule": "", # Will be filled if available in detailed view
            "Travel": "",      # Will be filled if available in detailed view
            "Relocation": ""   # Will be filled if available in detailed view
        }
        
        # Add all other fields that might be useful
        for key, value in job.items():
            if key not in ["externalPath", "title", "locationsText", "postedOn", "bulletFields"]:
                job_entry[key] = value
                
        job_data.append(job_entry)

    # Process the JSON data
    if job_data:
        # Sort job_data by Posted Date (most recent first)
        def sort_key(job):
            posted = job.get("Posted Date", "")
            if "Today" in posted:
                return 0
            elif "Yesterday" in posted:
                return 1
            else:
                return 2
        
        job_data_sorted = sorted(job_data, key=sort_key)
        
        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(job_data_sorted, json_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully processed {len(job_data)} jobs to JSON: {output_file}")
        
        # Also save the raw response for debugging
        with open("../jobs/nvidia_jobs_raw.json", "w", encoding="utf-8") as raw_file:
            json.dump(json_data, raw_file, indent=2, ensure_ascii=False)
        print(f"Saved raw API response to: {raw_json_file_path}")
        
    else:
        print("No job data found.")

def convert_json_to_csv(json_data, csv_file_name):
    """Convert the processed JSON data to CSV format."""
    
    # Try to load from processed file if json_data is None
    if json_data is None:
        processed_file = "nvidia_jobs_processed.json"
        if os.path.exists(processed_file):
            with open(processed_file, "r", encoding="utf-8") as f:
                job_data = json.load(f)
        else:
            print("No processed job data found.")
            return
    else:
        # Extract job postings from raw response
        job_postings = json_data.get("jobPostings", [])
        
        if not job_postings:
            print("No job postings found in JSON data.")
            return
        
        # Process the data similar to process_jobs_data function
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
                "Job URL": f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{external_path}",
                "Requisition ID": bullet_fields[0] if bullet_fields else "",
                "Bullet Fields": ", ".join(bullet_fields) if bullet_fields else ""
            }
            
            # Add all other fields
            for key, value in job.items():
                if key not in ["externalPath", "title", "locationsText", "postedOn", "bulletFields"]:
                    job_entry[key] = value
                    
            job_data.append(job_entry)
    
    if not job_data:
        print("No job data to convert to CSV.")
        return
    
    # Get all unique field names from all job entries
    fieldnames = set()
    for job in job_data:
        fieldnames.update(job.keys())
    
    # Convert to sorted list for consistent column order
    fieldnames = sorted(list(fieldnames))
    
    # Write to CSV
    with open(csv_file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(job_data)
    
    print(f"Successfully converted {len(job_data)} jobs to CSV: {csv_file_name}")

def get_all_jobs(max_jobs=1000):
    """Get all available jobs using pagination."""
    all_jobs = []
    offset = 0
    limit = 100  # Maximum per request
    
    while len(all_jobs) < max_jobs:
        json_data = make_nvidia_api_request(limit=limit, offset=offset)
        
        if not json_data:
            break
            
        job_postings = json_data.get("jobPostings", [])
        if not job_postings:
            break
            
        all_jobs.extend(job_postings)
        total_available = json_data.get("total", 0)
        
        print(f"Retrieved {len(all_jobs)} jobs so far (total available: {total_available})")
        
        if len(all_jobs) >= total_available:
            break
            
        offset += limit
        time.sleep(1)  # Be respectful to the API
    
    return {"jobPostings": all_jobs, "total": len(all_jobs)}

def main():
    # Define file paths with proper directory structure
    jobs_dir = "../jobs"
    os.makedirs(jobs_dir, exist_ok=True)
    
    json_file_path = os.path.join(jobs_dir, "nvidia_jobs_processed.json")
    raw_json_file_path = os.path.join(jobs_dir, "nvidia_jobs_raw.json")
    csv_file_path = os.path.join(jobs_dir, "nvidia_jobs.csv")
    
    print(f"=== NVIDIA Jobs Scraper (Final) ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # Get all available jobs
    print("\n[*] Retrieving all available jobs...")
    json_data = get_all_jobs(max_jobs=2000)  # Get up to 2000 jobs
    
    if json_data and json_data.get("jobPostings"):
        print(f"\n[*] Processing {len(json_data['jobPostings'])} jobs...")
        process_jobs_data(json_data, json_file_path)
        
        print("\n[*] Converting job data to CSV...")
        convert_json_to_csv(json_data, csv_file_path)
        
        print(f"\n✅ Process complete!")
        print(f"📄 JSON file: {json_file_path}")
        print(f"📊 CSV file: {csv_file_path}")
        print(f"🔍 Raw data: {raw_json_file_path}")
    else:
        print("❌ Failed to retrieve job data from NVIDIA API.")
        
        # Try to load from existing files if available
        if os.path.exists(raw_json_file_path):
            print(f"\n[*] Loading job data from existing {raw_json_file_path}...")
            with open(raw_json_file_path, "r", encoding="utf-8") as f:
                try:
                    json_data = json.load(f)
                    process_jobs_data(json_data, json_file_path)
                    convert_json_to_csv(json_data, csv_file_path)
                    print(f"\n✅ Process complete! Check {csv_file_path} for the job listings.")
                except Exception as e:
                    print(f"Error loading JSON from file: {e}")
        else:
            print("No existing job data files found.")

if __name__ == "__main__":
    main() 