import pprint
import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional


load_dotenv()

class JobPostingSystem:
    def __init__(self):
        self.AIRTABLE_BASE_ID = os.getenv('APP_EXAMPLE_BASE_ID')
        self.AIRTABLE_TABLE_ID = os.getenv('TABLE_EXAMPLE_TABLE_ID')
        self.AIRTABLE_API_KEY = os.getenv('AIR_TABLE_API')
        self.JBOARD_API_KEY = os.getenv('JBOARD_API_KEY')
        
        self.AIRTABLE_URL = f'https://api.airtable.com/v0/{self.AIRTABLE_BASE_ID}/{self.AIRTABLE_TABLE_ID}'
        self.JBOARD_URL = 'https://app.jboard.io/api/jobs'
        
        # Load employer data from JSON file
        self.employers = self.load_employer_data()

    def load_employer_data(self) -> Dict[str, int]:
        """Load employer data from JSON file."""
        try:
            with open('employers.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: employers.json file not found!")
            return {}

    def fetch_jobs_from_airtable(self) -> List[Dict]:
        """Fetch jobs from Airtable."""
        headers = {
            'Authorization': f'Bearer {self.AIRTABLE_API_KEY}'
        }
        
        try:
            response = requests.get(self.AIRTABLE_URL, headers=headers)
            response.raise_for_status()
            return response.json().get('records', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Airtable: {e}")
            return []

    def get_employer_id(self, company_name: str) -> Optional[int]:
        """Get employer ID from the loaded employer data."""
        return self.employers.get(company_name)

    def post_job_to_jboard(self, job_data: Dict) -> Optional[Dict]:
        """Post a single job to Jboard with detailed logging."""
        headers = {
            'Authorization': f'Bearer {self.JBOARD_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            print(f"\nPosting job: {job_data['title']} for {job_data['company']}")
            response = requests.post(self.JBOARD_URL, headers=headers, json=job_data)
            
            if response.status_code != 201:
                print(f"ERROR: Job posting failed for {job_data['title']}")
                print(f"Status Code: {response.status_code}")
                print("Response:", response.text)
                return None
                
            print(f"SUCCESS: Posted job: {job_data['title']}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"REQUEST EXCEPTION: {str(e)}")
            return None

    def process_jobs(self):
        """Process all jobs from Airtable and post them to Jboard."""
        print("Fetching jobs from Airtable...")
        jobs = self.fetch_jobs_from_airtable()
        
        if not jobs:
            print("No jobs found in Airtable.")
            return
        
        print(f"Found {len(jobs)} jobs. Starting upload to Jboard...")
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for job in jobs:
            airtable_fields = job.get('fields', {})
            company_name = airtable_fields.get("Company", "")
            employer_id = self.get_employer_id(company_name)
            
            if not employer_id:
                print(f"\nSkipping job - Unknown employer: {company_name}")
                continue
            
            job_data = {
                "title": airtable_fields.get("Title", ""),
                "description": airtable_fields.get("Snippet", ""),
                "link": airtable_fields.get("Link", ""),
                "category_id": 151223,
                "employer_id": employer_id,
                "posted_at": current_date,
                "job_expires_in_days": 30,
                "location": "Remote",
                "company": company_name,
                "apply_by": "by_link",
                "confirmation_status": "confirmed",
                "apply_to": airtable_fields.get("Link", ""),
                "featured": False,
                "remote": True,
                "pin_to_top": False,
            }
            
            if not all([job_data['title'], job_data['description'], job_data['link']]):
                print(f"\nSkipping job with missing required fields: {job_data['title']}")
                continue
                
            self.post_job_to_jboard(job_data)

def main():
    job_system = JobPostingSystem()
    job_system.process_jobs()

if __name__ == "__main__":
    main()