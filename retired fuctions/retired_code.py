import requests
import json
import time
import logging
import os
import re
from dotenv import load_dotenv
from pyairtable import Api
from helpers.api_helper import custom_requests_get

api = Api(os.getenv('AIR_TABLE_API', 'default_value'))
table = api.table('app816KaoBp3EZKwg','tblLbE2xSdrbR26ve')

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def is_valid_job_url(url, site):
    """
    Check if the URL is a valid job posting and not a job board page
    """
    url = url.lower()
    
    # Pattern matching for different job boards
    patterns = {
        'lever.co': r'https?://[^/]+\.lever\.co/[^/]+/[a-zA-Z0-9-]+(?!/apply|/job-board|/jobs|/careers)$',
        'greenhouse.io': r'https?://[^/]+\.greenhouse\.io/[^/]+/jobs/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'jobs.ashbyhq.com': r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$'
    }
    
    # Get the pattern for the current site
    pattern = patterns.get(site)
    if not pattern:
        return True  # If we don't have a pattern for this site, accept all URLs
    
    # Check if the URL matches the pattern
    return bool(re.match(pattern, url))

def search_jobs(api_key=None, search_engine_id=None, max_results=300):
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    max_results = int(os.getenv('MAX_RESULTS', max_results))
    
    job_sites = os.getenv('JOB_SITES', '').split(',')
    roles = os.getenv('JOB_ROLES', '').split(',')
    locations = os.getenv('LOCATIONS', '').split(',')
    
    job_results = []
    unique_links = set()
    
    # Create broader role variations
    expanded_roles = []
    for role in roles:
        role = role.strip()
        expanded_roles.extend([
            role,
            f'senior {role}',
            f'sr {role}',
            role.lower(),
            role.replace(' ', '-')
        ])
    expanded_roles = list(set(expanded_roles))  # Remove duplicates
    
    # Process each site separately but with broader conditions
    for site in job_sites:
        site = site.strip()
        if not site:
            continue
            
        for location in locations:
            location = location.strip()
            if not location:
                continue
                
            roles_query = ' OR '.join(f'"{role}"' for role in expanded_roles)
            # Add -"job board" -"all jobs" to exclude job board pages
            query = f'site:{site} "{location}" ({roles_query}) -"job board" -"all jobs" -"careers" -"jobs"'
            
            logger.info(f"🔍 Searching {site} for {location}...")
            
            start_index = 1
            while len(job_results) < max_results and start_index <= 100:
                params = {
                    'q': query,
                    'key': api_key,
                    'cx': search_engine_id,
                    'num': 10,
                    'start': start_index
                }
                
                response = custom_requests_get("https://www.googleapis.com/customsearch/v1", params=params)
                
                if response.status_code != 200:
                    logger.error(f"❌ Error {response.status_code} while searching {site}")
                    break
                    
                results = response.json()
                items = results.get('items', [])
                
                if not items:
                    break
                    
                for item in items:
                    link = item.get('link', '')
                    
                    # Skip if the link is not a valid job posting URL
                    if not link or not is_valid_job_url(link, site):
                        continue
                        
                    if link not in unique_links:
                        unique_links.add(link)
                        job_results.append({
                            "Title": item.get('title', 'N/A'),
                            "Link": link,
                            "Snippet": item.get('snippet', 'N/A'),
                        })
                        
                        if len(job_results) >= max_results:
                            logger.info(f"✅ Reached maximum results limit: {max_results}")
                            return job_results[:max_results]
                
                start_index += len(items)
                time.sleep(1)
    
    logger.info(f"📊 Total results found: {len(job_results)}")
    return job_results[:max_results]

def save_to_airtable(data):
    try:
        existing_records = table.all()
        existing_links = {record['fields'].get('Link') for record in existing_records}
        
        new_jobs = [job for job in data if job['Link'] not in existing_links]
        
        if new_jobs:
            chunk_size = 10
            for i in range(0, len(new_jobs), chunk_size):
                chunk = new_jobs[i:i + chunk_size]
                table.batch_create(chunk)
                time.sleep(0.5)
            logger.info(f"✅ Saved {len(new_jobs)} new job listings to Airtable")
        else:
            logger.info("ℹ️ No new job listings to save")
            
    except Exception as e:
        logger.error(f"❌ Error saving to Airtable: {e}")

def main():
    try:
        logger.info("🚀 Starting job search...")
        job_results = search_jobs()
        save_to_airtable(job_results)
        logger.info(f"✨ Completed! Found {len(job_results)} unique job listings")
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")

if __name__ == "__main__":
    main()