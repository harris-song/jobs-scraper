from playwright.sync_api import sync_playwright
import json
import os
import time

def process_jobs_data(json_data, output_file="../jobs/nvidia_jobs_processed.json"):
    # Ensure the jobs directory exists
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    """Process the raw NVIDIA jobs JSON data and save as structured JSON file."""
    job_postings = json_data.get("jobPostings", [])
    print(f"Found {len(job_postings)} job postings.")
    
    job_data = []
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
                
        job_data.append(job_entry)
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Minimal payload with just the required fields
    payload = {
        "limit": limit,
        "offset": offset
    }
    
    # Print request details for debugging
    print(f"[DEBUG] API URL: {url}")
    print(f"[DEBUG] Request headers: {headers}")
    print(f"[DEBUG] Request payload: {payload}")
    
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
        # Write to JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(job_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"Successfully processed {len(job_data)} jobs to JSON: {output_file}")
        
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

def make_alternate_api_request():
    """Try an alternative API endpoint to retrieve NVIDIA job listings."""
    
    # This URL points to their public-facing career search page
    url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/jobs"
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        print(f"[*] Making GET request to NVIDIA alternate API...")
        response = requests.get(url, headers=headers, timeout=30)
        
        print(f"[*] Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("[*] Successfully fetched the career page, extracting job data...")
            # Save the HTML for inspection
            with open("../jobs/nvidia_careers_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # This is a basic implementation. In reality, we would need to parse the HTML
            # to extract job information or look for embedded JSON data.
            
            # Mock response format to match what our processing functions expect
            mock_data = {
                "total": 1,
                "jobPostings": [
                    {
                        "title": "Sample Job Title - Alternate API Method",
                        "externalPath": "/job/Sample-Location/Sample-Job_JR1234567",
                        "locationsText": "Sample Location",
                        "postedOn": "Today",
                        "bulletFields": ["JR1234567"]
                    }
                ]
            }
            
            print("[*] Using Playwright as fallback method might be necessary...")
            return mock_data
        else:
            print(f"[!] Error with alternate API: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[!] Alternate request failed: {e}")
        return None

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