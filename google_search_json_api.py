import requests
import json
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()


logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def search_jobs(base_query=None, api_key=None, search_engine_id=None, max_results=300):
    # Use environment variables if parameters not provided
    api_key = api_key or os.getenv('GOOGLE_API_KEY')
    search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    max_results = int(os.getenv('MAX_RESULTS', max_results))
    base_query = base_query or os.getenv('BASE_QUERY')

    if not all([api_key, search_engine_id]):
        raise ValueError("API key and Search Engine ID are required. Set them in .env file or pass as parameters.")

    location_variations = [
        "LATAM", "Latin America",
        "Mexico", "Guadalajara",
        "Hermosillo", "Monterrey",
        "Mexico City"
    ]
    
    job_roles = [
        "engineer", "software engineer",
        "software developer", "developer",
        "backend engineer", "frontend engineer"
    ]

    job_results = []
    unique_links = set()

    for location in location_variations:
        for role in job_roles:
            query = f'site:lever.co "{location}" AND "{role}"'
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'q': query,
                'key': api_key,
                'cx': search_engine_id,
                'num': 10
            }

            try:
                logger.info(f"Searching with query: {query}")
                response = requests.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Error: {response.status_code} - {response.text}")
                    continue

                results = response.json()
                items = results.get('items', [])

                for item in items:
                    link = item.get('link', '')
                    if link and link not in unique_links:
                        unique_links.add(link)
                        job_results.append({
                            "title": item.get('title', 'N/A'),
                            "link": link,
                            "snippet": item.get('snippet', 'N/A')
                        })

                time.sleep(1)  # Rate limiting
                
                if len(job_results) >= max_results:
                    break

            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
                continue
            except json.JSONDecodeError:
                logger.error("Error decoding JSON response")
                continue
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

        if len(job_results) >= max_results:
            break

    return job_results[:max_results]

def save_to_json(data, filename='job_listings.json'):
    """
    Save job listings to a JSON file with UTF-8 encoding
    :param data: List of job dictionaries
    :param filename: Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved {len(data)} job listings to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON: {e}")

def main():
    try:
        job_results = search_jobs()
        save_to_json(job_results)
        logger.info(f"Total unique job listings retrieved: {len(job_results)}")
    except Exception as e:
        logger.error(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()