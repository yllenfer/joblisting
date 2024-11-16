import time
import logging
#import os
from dotenv import load_dotenv
from pyairtable import Api
#from ..helpers.api_helper import custom_requests_get
import json

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from helpers.api_helper import custom_requests_get
from helpers.validation import fetch_full_description, extract_compensation, extract_location 

api = Api(os.getenv('AIR_TABLE_API', 'default_value'))
table = api.table('app816KaoBp3EZKwg','tbla1yH8WjUmcrqYf')

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)



def search_jobs(api_key=None, search_engine_id=None, max_results=400):
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    max_results = int(os.getenv('MAX_RESULTS', max_results))
    
    job_sites = os.getenv('OTHER_PLATFORMS', '').split(',')
    job_sites_two = os.getenv('OTHER_PLATFORMS_TWO', '').split(',')
    job_sites_three = os.getenv('OTHER_PLATFORMS_THREE', '').split(',')
    job_sites_four = os.getenv('OTHER_PLATFORMS_FOUR', '').split(',')
    job_sites_combined = job_sites + job_sites_two + job_sites_three + job_sites_four
    locations = os.getenv('LOCATIONS', '').split(',')
    roles = os.getenv('JOB_ROLES', '').split(',')
    
    job_results = []
    unique_links = set()
    
    for site in job_sites_combined:
        site = site.strip()
        if not site:
            continue

        location_query = ' OR '.join([f'"{location}"' for location in locations])
        role_query = ' OR '.join([f'"{role}"' for role in roles])
        
        # Combined query with salary-related terms
        query = f'site:{site} ({location_query}) ({role_query}) (salary OR compensation OR pay OR "$")'
        logger.info(f"🔍 Query: {query}")
        
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
                logger.error(f"❌ Error {response.status_code} for query: {query}")
                break
            
            results = response.json()
            items = results.get('items', [])
            
            if not items:
                break
            
            for item in items:
                link = item.get('link', '')
                
                if not link or link in unique_links:
                    continue
                
                unique_links.add(link)
                
                # Combine title and snippet for better text analysis
                full_text = f"{item.get('title', '')} {item.get('snippet', '')}"
                
                # Get full description
                description = fetch_full_description(link) or item.get('snippet', 'N/A')
                
                # Extract compensation and location
                compensation = extract_compensation(full_text) or extract_compensation(description) or 'N/A'
                location = extract_location(full_text) or extract_location(description) or 'N/A'
                
                # Determine compensation currency
                currency = 'USD' if '$' in compensation else 'N/A'
                
                job_results.append({
                    "Title": item.get('title', 'N/A'),
                    "Link": link,
                    "Company": item.get('snippet', 'N/A').split('\n')[0], 
                    "Location": location,
                    "Description": description,
                    "Compensation": compensation,
                    "Compensation Currency": currency
                })
                
                if len(job_results) >= max_results:
                    logger.info(f"✅ Reached maximum results limit: {max_results}")
                    return job_results[:max_results]
            
            start_index += 10
            time.sleep(1) 

    # file_path = 'job_listings.json'
    
    # with open(file_path, "w") as f:
    #     json.dump(job_results, f, indent=4)

    logger.info(f"📊 Total unique job results found: {len(job_results)}")
    # logger.info(f"💾 Saved results to {file_path}")
    return job_results


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