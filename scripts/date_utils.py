"""
Date utility functions for standardizing job posting dates across all scrapers.
Converts various date formats to UTC ISO format (YYYY-MM-DDTHH:MM:SSZ).
"""

import re
from datetime import datetime, timezone, timedelta
from dateutil import parser


def normalize_date_to_utc(date_string):
    """
    Convert various date formats to standardized UTC ISO format.
    
    Args:
        date_string (str): Date string in various formats
        
    Returns:
        str: UTC ISO formatted date string (YYYY-MM-DDTHH:MM:SSZ) or empty string if parsing fails
    """
    if not date_string or not isinstance(date_string, str):
        return ""
    
    # Get current UTC time
    now_utc = datetime.now(timezone.utc)
    
    # Clean the input string
    date_string = date_string.strip()
    
    try:
        # Handle relative dates like "Posted Today", "Posted Yesterday", "Posted X Days Ago"
        if re.search(r'posted\s+today', date_string, re.IGNORECASE):
            # Posted today - use current date at midnight UTC
            result_date = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif re.search(r'posted\s+yesterday', date_string, re.IGNORECASE):
            # Posted yesterday
            result_date = (now_utc - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif re.search(r'posted\s+(\d+)\s+days?\s+ago', date_string, re.IGNORECASE):
            # Posted X days ago
            match = re.search(r'posted\s+(\d+)\s+days?\s+ago', date_string, re.IGNORECASE)
            days_ago = int(match.group(1))
            result_date = (now_utc - timedelta(days=days_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif re.search(r'posted\s+(\d+)\s+hours?\s+ago', date_string, re.IGNORECASE):
            # Posted X hours ago
            match = re.search(r'posted\s+(\d+)\s+hours?\s+ago', date_string, re.IGNORECASE)
            hours_ago = int(match.group(1))
            result_date = now_utc - timedelta(hours=hours_ago)
            
        elif re.search(r'posted\s+(\d+)\s+weeks?\s+ago', date_string, re.IGNORECASE):
            # Posted X weeks ago
            match = re.search(r'posted\s+(\d+)\s+weeks?\s+ago', date_string, re.IGNORECASE)
            weeks_ago = int(match.group(1))
            result_date = (now_utc - timedelta(weeks=weeks_ago)).replace(hour=0, minute=0, second=0, microsecond=0)
            
        elif re.search(r'posted\s+(\d+)\s+months?\s+ago', date_string, re.IGNORECASE):
            # Posted X months ago (approximate)
            match = re.search(r'posted\s+(\d+)\s+months?\s+ago', date_string, re.IGNORECASE)
            months_ago = int(match.group(1))
            result_date = (now_utc - timedelta(days=months_ago * 30)).replace(hour=0, minute=0, second=0, microsecond=0)
            
        else:
            # Try to parse as regular date using dateutil parser
            # Remove "Posted" prefix if present
            clean_date = re.sub(r'^posted\s+', '', date_string, flags=re.IGNORECASE).strip()
            
            # Parse the date
            parsed_date = parser.parse(clean_date)
            
            # If no timezone info, assume it's in the local timezone and convert to UTC
            if parsed_date.tzinfo is None:
                # Assume local time and convert to UTC (using system timezone)
                result_date = parsed_date.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if timezone is specified
                result_date = parsed_date.astimezone(timezone.utc)
        
        # Return in ISO format with Z suffix for UTC
        return result_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
    except Exception as e:
        print(f"[Warning] Failed to parse date '{date_string}': {e}")
        return ""


def get_current_utc_timestamp():
    """
    Get current UTC timestamp in ISO format.
    
    Returns:
        str: Current UTC timestamp in ISO format (YYYY-MM-DDTHH:MM:SSZ)
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def add_scrape_metadata(job_entry):
    """
    Add metadata about when the job was scraped.
    
    Args:
        job_entry (dict): Job entry dictionary
        
    Returns:
        dict: Job entry with added scrape metadata
    """
    job_entry["Scraped At"] = get_current_utc_timestamp()
    
    # Normalize the Posted Date if it exists (including empty strings)
    if "Posted Date" in job_entry:
        original_date = job_entry["Posted Date"]
        
        # Only process if there's actually a date string
        if original_date and original_date.strip():
            normalized_date = normalize_date_to_utc(original_date)
            
            # Keep both original and normalized for debugging/reference
            job_entry["Posted Date Original"] = original_date
            job_entry["Posted Date"] = normalized_date
        else:
            # Handle empty dates - keep empty but add original field for consistency
            job_entry["Posted Date Original"] = original_date
            # Leave Posted Date as empty string
    
    return job_entry


# Test function for debugging
def test_date_normalization():
    """Test the date normalization function with various inputs."""
    test_cases = [
        "Posted Today",
        "Posted Yesterday", 
        "Posted 2 Days Ago",
        "Posted 1 week ago",
        "Posted 3 months ago",
        "Jun 29, 2025",
        "2025-06-29",
        "29 Jun 2025",
        "June 29, 2025",
        "2025-06-29T14:30:00Z",
        "2025-06-29 14:30:00",
        ""
    ]
    
    print("Testing date normalization:")
    print("=" * 50)
    
    for test_date in test_cases:
        result = normalize_date_to_utc(test_date)
        print(f"'{test_date}' -> '{result}'")
    
    print("=" * 50)
    print(f"Current UTC: {get_current_utc_timestamp()}")


if __name__ == "__main__":
    test_date_normalization()
