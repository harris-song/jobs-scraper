"""
Script to update existing job JSON files with standardized UTC dates.
This will process all existing job JSON files and apply the date normalization.
"""

import json
import os
import glob
from date_utils import add_scrape_metadata


def update_existing_json_files():
    """Update all existing JSON files with standardized dates."""
    jobs_dir = "../jobs"
    
    # Find all processed JSON files
    json_files = glob.glob(os.path.join(jobs_dir, "*_jobs_processed.json"))
    
    print(f"Found {len(json_files)} JSON files to update:")
    
    for json_file in json_files:
        print(f"\nProcessing: {json_file}")
        
        try:
            # Read the existing data
            with open(json_file, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
            
            if not isinstance(jobs_data, list):
                print(f"Skipping {json_file} - not a list of jobs")
                continue
            
            print(f"Found {len(jobs_data)} jobs in {os.path.basename(json_file)}")
            
            # Update each job entry
            updated_jobs = []
            for job in jobs_data:
                if isinstance(job, dict):
                    # Apply date standardization and add scrape metadata
                    updated_job = add_scrape_metadata(job)
                    updated_jobs.append(updated_job)
                else:
                    updated_jobs.append(job)
            
            # Write back the updated data
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(updated_jobs, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Updated {json_file}")
            
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎉 Finished updating {len(json_files)} JSON files")


def show_date_formats_summary():
    """Show a summary of date formats in all JSON files."""
    jobs_dir = "../jobs"
    json_files = glob.glob(os.path.join(jobs_dir, "*_jobs_processed.json"))
    
    print("Date formats summary:")
    print("=" * 50)
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
            
            if not isinstance(jobs_data, list) or not jobs_data:
                continue
            
            company = os.path.basename(json_file).replace("_jobs_processed.json", "").title()
            
            # Check first job for date format info
            first_job = jobs_data[0]
            posted_date = first_job.get("Posted Date", "")
            original_date = first_job.get("Posted Date Original", "")
            scraped_at = first_job.get("Scraped At", "")
            
            print(f"\n{company}:")
            print(f"  Posted Date: {posted_date}")
            if original_date:
                print(f"  Original: {original_date}")
            print(f"  Scraped At: {scraped_at}")
            print(f"  Total jobs: {len(jobs_data)}")
            
        except Exception as e:
            print(f"Error reading {json_file}: {e}")


if __name__ == "__main__":
    print("🔄 Updating existing job JSON files with standardized dates...")
    update_existing_json_files()
    
    print("\n" + "=" * 60)
    show_date_formats_summary()
