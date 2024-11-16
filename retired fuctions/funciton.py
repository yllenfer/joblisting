import requests
import json
import time
import logging
import os
from dotenv import load_dotenv
from pyairtable import Api
from helpers.api_helper import custom_requests_get
import re


api = Api(os.getenv('AIR_TABLE_API', 'default_value'))
table = api.table('app816KaoBp3EZKwg','tblLbE2xSdrbR26ve')

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def search_jobs(base_query=None, api_key=None, search_engine_id=None, max_results=300):
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    max_results = int(os.getenv('MAX_RESULTS', max_results))
    
    job_sites = os.getenv('JOB_SITES', '').split(',')
    roles = os.getenv('JOB_ROLES', '').split(',')
    
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
        roles_query = ' OR '.join(f'"{role}"' for role in expanded_roles)
        query = f'site:{site.strip()} ("LATAM" OR "Latin America" OR "Remote LATAM" OR "Latin American" OR "Americas") ({roles_query})'
        
        start_index = 1
        while len(job_results) < max_results:
            params = {
                'q': query,
                'key': api_key,
                'cx': search_engine_id,
                'num': 10,
                'start': start_index
            }
            
            try:
                logger.info(f"Searching {site.strip()} for {len(expanded_roles)} role variations")
                response = custom_requests_get("https://www.googleapis.com/customsearch/v1", params=params)
                
                if response.status_code != 200:
                    logger.error(f"Error: {response.status_code} - {response.text}")
                    break
                    
                results = response.json()
                items = results.get('items', [])
                
                if not items:  # No more results
                    break
                    
                for item in items:
                    link = item.get('link', '')
                    if link and link not in unique_links:
                        unique_links.add(link)
                        job_results.append({
                            "Title": item.get('title', 'N/A'),
                            "Link": link,
                            "Snippet": item.get('snippet', 'N/A')
                        })
                
                if len(job_results) >= max_results:
                    break
                    
                start_index += len(items)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error during search: {str(e)}")
                break
                
        if len(job_results) >= max_results:
            break
            
  
  
    return job_results[:max_results]

def save_to_airtable(data):
    try:
        for job in data:
            table.create(job)
        logger.info(f"Successfully saved {len(data)} job listings to Airtable")
    except Exception as e:
        logger.error(f"Error saving to Airtable: {e}")

def main():
    try:
        job_results = search_jobs()
        save_to_airtable(job_results)
        logger.info(f"Total unique job listings retrieved: {len(job_results)}")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()