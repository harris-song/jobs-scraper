import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_browser():
    """Set up a browser instance with Selenium."""
    try:
        # First try using Firefox
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService
        
        print("Attempting to use Firefox for scraping...")
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.set_preference("general.useragent.override", 
                              "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        
        print("Starting Firefox browser...")
        driver = webdriver.Firefox(options=options)
        return driver
    except Exception as e:
        print(f"Firefox setup failed: {e}. Falling back to Chrome...")
        
        # Fall back to Chrome if Firefox is not available
        try:
            from selenium.webdriver.chrome.options import Options
            options = Options()
            options.add_argument("--headless")  # Run in headless mode
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
            
            print("Starting Chrome browser...")
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            print(f"Chrome setup failed: {e}.")
            raise

def scrape_meta_jobs():
    """Scrape Meta jobs using Selenium to simulate browser behavior."""
    driver = setup_browser()
    
    try:
        # Navigate to the Meta careers page
        url = "https://www.metacareers.com/jobs?teams[0]=University%20Grad%20-%20Business&teams[1]=University%20Grad%20-%20Engineering%2C%20Tech%20%26%20Design&teams[2]=University%20Grad%20-%20PhD%20%26%20Postdoc&sort_by_new=true"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)  # Give it some time to load
        
        # Wait longer for the page to load
        print("Waiting for page to fully load...")
        time.sleep(5)  # Give more time for JavaScript to execute
        
        # Check if page has loaded properly
        print("Checking page content...")
        page_title = driver.title
        print(f"Page title: {page_title}")
        
        # Try multiple potential selectors for job cards
        print("Extracting job data...")
        job_elements = []
        
        # List of possible selectors for job cards
        selectors = [
            "[data-testid='careers-job-card']",
            ".css-1vwkltq",
            ".careers-jobs-results-list__item",
            ".job-card",
            "article",  # Generic fallback
            "div[role='article']"  # Another common pattern
        ]
        
        # Try each selector
        for selector in selectors:
            print(f"Trying selector: {selector}")
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found {len(elements)} job listings with selector {selector}")
                job_elements = elements
                break
        
        # If still no elements found, extract all links on the page as a fallback
        if not job_elements:
            print("No job cards found. Looking for job links...")
            # Look for links that might be job postings
            all_links = driver.find_elements(By.TAG_NAME, "a")
            job_links = [link for link in all_links if "/jobs/" in link.get_attribute("href") or "/careers/" in link.get_attribute("href")]
            print(f"Found {len(job_links)} potential job links")
            job_elements = job_links
        
        print(f"Found {len(job_elements)} job elements to process")
        
        # Capture page source for debugging before extraction
        with open("meta_page_before_extraction.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Saved page source for debugging")
        
        jobs = []
        for index, job_element in enumerate(job_elements[:20]):  # Process up to 20
            try:
                print(f"Processing job element {index+1}...")
                job_data = {"Job ID": "N/A", "Title": "N/A", "Location": "N/A", "Team": "N/A", "Job URL": "N/A"}
                
                # Extract job link (this is the most reliable piece of information)
                if job_element.tag_name == "a":  # If the element itself is a link
                    link = job_element.get_attribute("href")
                    job_data["Job URL"] = link
                    # Try to get the title from the link text
                    job_data["Title"] = job_element.text or "N/A"
                else:
                    # Try to find a link within this element
                    try:
                        link_element = job_element.find_element(By.TAG_NAME, "a")
                        link = link_element.get_attribute("href")
                        job_data["Job URL"] = link
                    except:
                        pass
                
                # Try different approaches to extract title
                try:
                    # Common title selectors
                    for title_selector in ["h3", "h2", "h4", "[data-testid='careers-job-title']", ".job-title"]:
                        try:
                            title_element = job_element.find_element(By.CSS_SELECTOR, title_selector)
                            if title_element and title_element.text.strip():
                                job_data["Title"] = title_element.text.strip()
                                break
                        except:
                            pass
                except:
                    pass
                
                # Try to extract location
                try:
                    # Common location selectors
                    for loc_selector in ["[data-testid='careers-job-location-text']", ".job-location", ".location"]:
                        try:
                            loc_element = job_element.find_element(By.CSS_SELECTOR, loc_selector)
                            if loc_element and loc_element.text.strip():
                                job_data["Location"] = loc_element.text.strip()
                                break
                        except:
                            pass
                except:
                    pass
                
                # Try to extract team
                try:
                    # Common team selectors
                    for team_selector in ["[data-testid='careers-job-team-text']", ".job-team", ".team"]:
                        try:
                            team_element = job_element.find_element(By.CSS_SELECTOR, team_selector)
                            if team_element and team_element.text.strip():
                                job_data["Team"] = team_element.text.strip()
                                break
                        except:
                            pass
                except:
                    pass
                
                # Extract job ID from URL if available
                if job_data["Job URL"] != "N/A" and "/" in job_data["Job URL"]:
                    job_data["Job ID"] = job_data["Job URL"].split("/")[-1]
                
                # Add the job data to our list
                jobs.append(job_data)
                print(f"Extracted job: {job_data['Title']} ({job_data['Location']})")
                
            except Exception as e:
                print(f"Error extracting job details: {str(e)}")
        
        # Save the results
        if jobs:
            with open("meta_jobs_processed.json", "w", encoding="utf-8") as f:
                json.dump(jobs, f, indent=2)
            print(f"Saved {len(jobs)} jobs to meta_jobs_processed.json")
        else:
            print("No jobs were extracted")
            
        # Capture and save page HTML for debugging
        html = driver.page_source
        with open("meta_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved page HTML to meta_page.html for debugging")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        print("Closing browser...")
        driver.quit()
        
        # Delete the intermediate HTML files
        delete_debug_files()

def delete_debug_files():
    """Delete the intermediate HTML files used for debugging."""
    debug_files = ["meta_page_before_extraction.html", "meta_page.html"]
    for file in debug_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted debug file: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {str(e)}")

if __name__ == "__main__":
    scrape_meta_jobs()
    delete_debug_files()
