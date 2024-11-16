# Job Search and Posting System

## Overview
This project is a comprehensive job search and posting system that automates the process of finding job listings from various sources, storing them in Airtable, and then posting them to Jboard. It consists of two main components:

1. Google Search API Integration for job discovery
2. Job Posting System for uploading jobs to Jboard

## Features

- Automated job search using Google Custom Search API
- Flexible search parameters including job sites, locations, and roles
- Data storage in Airtable
- Job posting to Jboard with employer matching
- Detailed logging and error handling

## Project Structure
google search request/
├── google_search_json_api.py
├── requirements.txt
helpers/
├── api_helper.py
├── validation.py
jboard request/
├── employers.json
├── jboards_schema.json
├── send_to_jboard.py
retired functions/
├── function.py
├── retired_code.py
test google request/
├── test_google_request.py

## Setup

1. Clone the repository
2. Install dependencies:

pip3 install -r requirements.txt

3. Set up environment variables in a `.env` file:
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
AIR_TABLE_API=your_airtable_api_key
APP_EXAMPLE_BASE_ID=your_airtable_base_id
TABLE_EXAMPLE_TABLE_ID=your_airtable_table_id
JBOARD_API_KEY=your_jboard_api_key
JOB_SITES=site1.com,site2.com
LOCATIONS=Location1,Location2
JOB_ROLES=Role1,Role2
MAX_RESULTS=Max_results
LOG_LEVEL=INFO

## Usage

1. To run the job search and store results in Airtable:
python google_search_json_api.py

2. To post jobs from Airtable to Jboard:
python send_to_jboard.py

## Main Components

### Google Search API Integration (`google_search_json_api.py`)

- Searches for job listings using Google Custom Search API
- Stores results in a JSON file and Airtable
- Configurable search parameters via environment variables

### Job Posting System (`send_to_jboard.py`)

- Fetches job listings from Airtable
- Matches employers using `employers.json`
- Posts jobs to Jboard API

## TODO

- Modify snippet to grab the full job description
- Extract compensation information if available
- Improve location extraction
- Set up weekly sync schedule
- Review and optimize job site queries

## Contributing

Contributions to improve the project are welcome. Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



## Contact

Yllen Fernandez - yllenfernandez@gmail.com

Project Link: [https://github.com/yllenfer/joblisting](https://github.com/yllenfer/joblisting)