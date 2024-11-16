import re
import requests
from bs4 import BeautifulSoup
import logging
import os

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def clean_job_title(title):
    """
    Clean job titles by removing company names, locations, and other common patterns.
    
    Args:
        title (str): Raw job title string
    Returns:
        str: Cleaned job title
    """
 
    separators = [' at ', ' in ', ' - ', ' | ', ' @ ', ' for ']
    cleaned_title = title
    for separator in separators:
        if separator in cleaned_title:
            cleaned_title = cleaned_title.split(separator)[0]
    

    location_patterns = [
        r'\([^)]*\)',  
        r'\[[^\]]*\]', 
        r'(?i)\b(remote|hybrid|onsite|on-site|in-office)\b.*$',  
        r'(?i)\b(full[ -]time|part[ -]time|contract)\b.*$', 
        r'(?i)\b(united states|usa|uk|europe|apac)\b.*$',  
        r'\d{1,2}\+? years?.*$',  
        r',.*$' 
    ]
    
    for pattern in location_patterns:
        cleaned_title = re.sub(pattern, '', cleaned_title)
    

    cleaned_title = ' '.join(cleaned_title.split())
    
    return cleaned_title.strip()




def is_valid_job_url(url, site):
    """
    Check if the URL is a valid job posting and not a job board page
    """
    url = url.lower()
    
    
    patterns = {
        'lever.co': r'https?://[^/]+\.lever\.co/[^/]+/[a-zA-Z0-9-]+(?!/apply|/job-board|/jobs|/careers)$',
        'greenhouse.io': r'https?://[^/]+\.greenhouse\.io/[^/]+/jobs/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'jobs.ashbyhq.com': r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'workday.com':  r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'smartrecruiters.com':  r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'indeed.com':  r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$',
        'boards.greenhouse.io':  r'https?://[^/]+\.ashbyhq\.com/[^/]+/[0-9]+(?!/apply|/job-board|/jobs|/careers)$'
    }
    
  
    pattern = patterns.get(site)
    if not pattern:
        return True  
  
    return bool(re.match(pattern, url))


def extract_company(text, url):
    """Extract company name from job posting."""
    # Common patterns for company names in job titles
    patterns = [
        r'at\s+([A-Za-z0-9\s&]+?)\s*(?:is|for|in)',
        r'with\s+([A-Za-z0-9\s&]+?)\s*(?:is|for|in)',
        r'-\s*([A-Za-z0-9\s&]+?)\s*(?:is|for|in|\d|$)',
        r'\|\s*([A-Za-z0-9\s&]+?)\s*(?:is|for|in|\d|$)'
    ]
    
    # Try to extract from domain first
    try:
        domain = url.split('//')[1].split('/')[0]
        if any(job_site in domain for job_site in ['linkedin', 'indeed', 'glassdoor']):
            # For job boards, try to extract from text
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        else:
            # If not a job board, use the domain name
            company = domain.split('.')[0]
            if company not in ['www', 'jobs', 'careers']:
                return company.title()
    except:
        pass
    
    # Fallback to text patterns
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return 'N/A'

def extract_location(text):
    """Extract location information from text."""
    # Enhanced location patterns
    location_patterns = [
        # Remote/Hybrid patterns
        r'(?:^|\W)((?:fully\s+)?remote)(?:\W|$)',
        r'(?:^|\W)(hybrid)(?:\W|$)',
        r'(?:^|\W)(on[- ]site|in[- ]office)(?:\W|$)',
        
        # City, State patterns
        r'(?:in|at|location:?\s*)\s*([A-Z][a-zA-Z\s]+,\s*[A-Z]{2})',
        r'(?:in|at|location:?\s*)\s*([A-Z][a-zA-Z\s]+(?:\s*-\s*[A-Z][a-zA-Z\s]+)?)',
        
        # International patterns
        r'(?:in|at|location:?\s*)\s*([A-Z][a-zA-Z\s]+,\s*[A-Za-z\s]+)'
    ]
    
    locations = []
    for pattern in location_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            location = match.group(1).strip()
            if location.lower() not in [loc.lower() for loc in locations]:
                locations.append(location)
    
    return ' / '.join(locations) if locations else 'N/A'



def extract_compensation(text):
    """Extract salary/compensation information from text."""
    # Enhanced salary patterns
    patterns = [
        # Ranges with K
        r'\$\d{2,3}k\s*-\s*\$\d{2,3}k',  # $50k - $70k
        r'\$\d{2,3}-\d{2,3}k',  # $50-70k
        
        # Full numbers with ranges
        r'\$\d{1,3}(?:,\d{3})*(?:\s*-\s*\$\d{1,3}(?:,\d{3})*)?(?:\s*per\s*year)?',
        
        # Ranges with + symbol
        r'\$\d{2,3}(?:,\d{3})*\+',  # $50,000+
        r'\$\d{2,3}k\+',  # $50k+
        
        # Hourly rates
        r'\$\d{2,3}(?:\.\d{2})?\s*(?:per\s*hour|\/\s*hr|\/\s*hour|\s*hr)',
        
        # Annual salary mentions
        r'annual\s*salary\s*(?:of\s*)?\$\d{1,3}(?:,\d{3})*',
        r'salary\s*range\s*(?:of\s*)?\$\d{1,3}(?:,\d{3})*\s*-\s*\$\d{1,3}(?:,\d{3})*'
    ]
    
    compensations = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            comp = match.group(0).strip()
            if comp not in compensations:
                compensations.append(comp)
    
    return ' / '.join(compensations) if compensations else 'N/A'


def determine_currency(compensation_text, description_text):
    """Determine the currency of compensation."""
    currency_patterns = {
        'USD': r'\$',
        'EUR': r'€',
        'GBP': r'£',
        'CAD': r'CAD|\$.*\s*CAD',
        'AUD': r'AUD|\$.*\s*AUD'
    }
    
    # Combine texts for searching
    full_text = f"{compensation_text} {description_text}"
    
    # Check each currency pattern
    for currency, pattern in currency_patterns.items():
        if re.search(pattern, full_text, re.IGNORECASE):
            return currency
    
    return 'N/A'


def fetch_full_description(url):
    """Fetch and parse the full job description from the job posting URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script, style, and nav elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            # Look for common job description containers
            description = None
            selectors = [
                ['div', {'class': re.compile(r'job-description|description|details|posting-details', re.I)}],
                ['section', {'class': re.compile(r'job-description|description|details', re.I)}],
                ['div', {'id': re.compile(r'job-description|description|details', re.I)}],
                ['article'],
                ['main']
            ]
            
            for tag, attrs in selectors:
                if description:
                    break
                elements = soup.find_all(tag, attrs) if attrs else soup.find_all(tag)
                if elements:
                    text = elements[0].get_text(separator=' ', strip=True)
                    if len(text) > 100:  # Ensure we have substantial content
                        description = text
            
            if description:
                # Clean up the text
                description = re.sub(r'\s+', ' ', description)  # Normalize whitespace
                description = re.sub(r'[^\w\s.,;!?-]', '', description)  # Remove special characters
                return description
            
        return None
    except Exception as e:
        logger.warning(f"Could not fetch full description from {url}: {e}")
        return None