import os
import re
import json
import time
import logging
import zipfile
import io
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.WARNING)

# Constants
REQUEST_DELAY = 0.12  # seconds between requests

# Contest cutoff - don't scrape contests after this date
CUTOFF_MONTH = 3
CUTOFF_YEAR = 25

def parse_contest_date(contest_name):
    """Parse month and year from contest name (e.g., 'DEC24 Bronze')"""
    month_map = {
        'DEC': 12,
        'JAN': 1,
        'FEB': 2,
        'OPEN': 3,  # OPEN happens in March
    }
    
    match = re.match(r'([A-Z]+)(\d+)', contest_name)
    if not match:
        return None, None
        
    month_str, year_str = match.groups()
    month = month_map.get(month_str)
    if month is None:
        return None, None
        
    try:
        year = int(year_str)
        return month, year
    except ValueError:
        return None, None

def is_contest_before_cutoff(contest_name):
    """Check if contest is before or at the cutoff date"""
    month, year = parse_contest_date(contest_name)
    if month is None or year is None:
        return False
        
    # Convert 2-digit year to comparable format
    if year > 90:  # Assume 90-99 means 1990-1999
        year += 1900
    else:  # Assume 00-89 means 2000-2089
        year += 2000
        
    cutoff_year = 2000 + CUTOFF_YEAR
    
    # Compare years first
    if year < cutoff_year:
        return True
    if year > cutoff_year:
        return False
        
    # If same year, compare months
    return month <= CUTOFF_MONTH

def parse_contest_info(contest_name):
    """Parse contest name into month, year, and division"""
    # Skip contests that don't match our expected format
    match = re.match(r'([A-Z]+)(\d+)\s+([A-Za-z]+)', contest_name)
    if not match:
        logging.warning(f"Contest name '{contest_name}' does not match expected format")
        return None
        
    month, year, division = match.groups()
    return {
        'month': month,
        'year': year,
        'division': division
    }

def get_linked_problem_id(session, problem_id):
    """Check if a problem is a link and return the linked problem ID if it is"""
    edit_url = f'https://probgate.org/probgate/edit.php?pid={problem_id}'
    
    try:
        response = session.get(edit_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        statement_text = soup.find('textarea', {'id': 'statement_text'})
        
        if statement_text:
            content = statement_text.text.strip()
            # Look for link pattern [a|https://probgate.org/viewproblem.php?pid=XXXX]Link[/a]
            link_match = re.search(r'\[a\|https://probgate\.org/viewproblem\.php\?pid=(\d+)\]Link\[/a\]', content)
            if link_match:
                return link_match.group(1)
        
        return None
        
    except requests.RequestException as e:
        logging.error(f"Error checking if problem {problem_id} is a link: {e}")
        return None

def get_contest_problems(session, contest_id):
    """Fetch and parse problems for a specific contest"""
    config_url = f'https://probgate.org/contest/config.php?cid={contest_id}'
    
    try:
        response = session.get(config_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        problems_div = soup.find('div', id='problems')
        
        if not problems_div:
            logging.warning(f"No problems div found for contest {contest_id}")
            return []
            
        problems = []
        for row in problems_div.find_all('tr')[1:]:  # Skip header row
            cols = row.find_all('td')
            if len(cols) >= 2:
                problem_id = cols[0].text.strip()
                problem_link = cols[1].find('a')
                if problem_link:
                    problem_name = problem_link.text.strip()
                    if problem_name.endswith(' (Link)'):
                        problem_name = problem_name[:-7]  # Remove ' (Link)' suffix
                        # Check if this is a linked problem
                        linked_id = get_linked_problem_id(session, problem_id)
                        if linked_id:
                            print(f"Problem {problem_name} (ID: {problem_id}) is a link to problem {linked_id}")
                            problem_id = linked_id
                    problems.append({
                        'problem_id': problem_id,
                        'name': problem_name
                    })
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(REQUEST_DELAY)
        return problems
        
    except requests.RequestException as e:
        logging.error(f"Error fetching problems for contest {contest_id}: {e}")
        return []

def get_problem_zip(session, problem_id):
    """Download and extract problem ZIP file"""
    export_url = f'https://probgate.org/probgate/export.php?pid={problem_id}'
    
    # Data for the export request
    data = {
        'statement': 'on',
        'analysis': 'on',
        'render': 'on',
        'attachments': 'on',
        'tests': 'on',
        'grader': 'on',
        'scorer': 'on',
        'validator': 'on',
        'solutions': 'on',
        'generators': 'on',
        'submissions': 'on',
        'archive': 'zip',
        'export': 'Export'
    }
    
    try:
        # Make the export request
        headers = {
            'Referer': f'https://probgate.org/probgate/export.php?pid={problem_id}'
        }
        response = session.post(export_url, data=data, headers=headers)
        response.raise_for_status()
        
        # Create the data_private/probgate/problems directory if it doesn't exist
        os.makedirs('data_private/probgate/problems', exist_ok=True)
        
        # Create temporary problem directory
        tmp_dir = os.path.join('data_private/probgate/problems', f"{problem_id}.tmp")
        final_dir = os.path.join('data_private/probgate/problems', str(problem_id))
        
        # Remove tmp_dir if it exists (from a previous failed attempt)
        if os.path.exists(tmp_dir):
            import shutil
            shutil.rmtree(tmp_dir)
        
        os.makedirs(tmp_dir)
        
        # Extract the ZIP file to temporary directory
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(tmp_dir)
        
        # Rename temporary directory to final directory
        if os.path.exists(final_dir):
            import shutil
            shutil.rmtree(final_dir)
        os.rename(tmp_dir, final_dir)
            
        print(f"Successfully downloaded and extracted problem {problem_id}")
        return True
        
    except requests.RequestException as e:
        logging.error(f"Error downloading problem {problem_id}: {e}")
        return False
    except zipfile.BadZipFile as e:
        logging.error(f"Error extracting ZIP for problem {problem_id}: {e}")
        return False
    except Exception as e:
        logging.error(f"Error processing problem {problem_id}: {e}")
        # Clean up temporary directory if it exists
        if os.path.exists(tmp_dir):
            import shutil
            shutil.rmtree(tmp_dir)
        return False

def scrape_problems(session, contests):
    """Download problem ZIP files"""
    for contest in contests.values():
        if 'problems' not in contest:
            continue
            
        for problem in contest['problems']:
            problem_id = problem['problem_id']
            problem_dir = os.path.join('data_private/probgate/problems', str(problem_id))
            
            # Skip if we already have this problem
            if os.path.exists(problem_dir):
                print(f"Skipping problem {problem['name']} (ID: {problem_id}) - already downloaded")
                continue
                
            print(f"Downloading problem {problem['name']} (ID: {problem_id})...")
            get_problem_zip(session, problem_id)
            
            # Add a small delay between downloads
            time.sleep(REQUEST_DELAY)

def load_existing_contests():
    """Load existing contests from JSON file if it exists"""
    try:
        with open('data_private/probgate/contests.json', 'r', encoding='utf-8') as f:
            return {contest['contest_id']: contest for contest in json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_contests(contests):
    """Save contests to JSON file"""
    os.makedirs('data_private/probgate', exist_ok=True)
    with open('data_private/probgate/contests.json', 'w', encoding='utf-8') as f:
        json.dump(list(contests.values()), f, indent=2)

def login_to_probgate():
    """Log in to Probgate and return a session"""
    session = requests.Session()
    
    # Get login credentials from environment variables
    username = os.getenv('PROBGATE_USERNAME')
    password = os.getenv('PROBGATE_PASSWORD')
    
    if not username or not password:
        raise ValueError("PROBGATE_USERNAME and PROBGATE_PASSWORD must be set in .env file")
    
    # Log in to Probgate
    login_url = 'https://probgate.org/login.php'
    login_data = {
        'user': username,
        'password': password,
    }
    
    try:
        # First, get the login page to capture any CSRF token if needed
        login_page = session.get(login_url)
        login_page.raise_for_status()
        
        # Perform login with referrer header
        headers = {
            'Referer': 'https://probgate.org/login.php'
        }
        response = session.post(login_url, data=login_data, headers=headers)
        response.raise_for_status()

        # Check if login was successful by looking for common failure indicators
        if 'incorrect' in response.text.lower() or 'failed' in response.text.lower():
            logging.error("Login failed. Please check your credentials.")
            return None
            
        return session
    except requests.RequestException as e:
        logging.error(f"Error logging in to Probgate: {e}")
        return None

def scrape_probgate():
    # Load existing contests
    existing_contests = load_existing_contests()
    
    # Create a session to maintain cookies
    session = login_to_probgate()
    if not session:
        return None, None
    
    # Get the target page
    target_url = 'https://probgate.org/contest/contestgate.php'
    
    try:
        # Get the target page
        contest_page = session.get(target_url)
        contest_page.raise_for_status()
        
        # Parse the page content
        soup = BeautifulSoup(contest_page.text, 'html.parser')
        
        # Find all contest tables - they have class 'subtable sortable'
        tables = soup.find_all('table', {'class': 'subtable sortable'})
        if not tables:
            print("No contest tables found")
            return None, None
            
        contests = {}
        for table in tables:
            # Skip header row
            for row in table.find_all('tr')[1:]:  
                cols = row.find_all('td')
                if len(cols) >= 2:
                    contest_id = cols[0].text.strip()
                    contest_link = cols[1].find('a')
                    if contest_link:
                        contest_name = contest_link.text.strip()
                        
                        # Skip contests after cutoff date
                        if not is_contest_before_cutoff(contest_name):
                            print(f"Skipping {contest_name} (ID: {contest_id}) - after cutoff date or invalid date")
                            continue
                        
                        # Skip if we already have this contest and its problems
                        if contest_id in existing_contests and 'problems' in existing_contests[contest_id]:
                            print(f"Skipping {contest_name} (ID: {contest_id}) - already scraped")
                            contests[contest_id] = existing_contests[contest_id]
                            continue
                        
                        info = parse_contest_info(contest_name)
                        if info:
                            print(f"Scraping {contest_name} (ID: {contest_id})...")
                            problems = get_contest_problems(session, contest_id)
                            
                            contests[contest_id] = {
                                'contest_id': contest_id,
                                'name': contest_name,
                                'month': info['month'],
                                'year': info['year'],
                                'division': info['division'],
                                'problems': problems
                            }
                            
                            # Save progress after each contest
                            save_contests(contests)
                            
                            # Add a small delay between requests
                            time.sleep(REQUEST_DELAY)
        
        print(f"\nSuccessfully saved {len(contests)} contests to 'data_private/probgate/contests.json'")
        return session, contests
        
    except requests.RequestException as e:
        logging.error(f"Error fetching contests: {e}")
        return None, None


def main():
    session, contests = scrape_probgate()
    if session and contests:
        # Download problem ZIPs
        print("\nDownloading problem files...")
        scrape_problems(session, contests)


if __name__ == "__main__":
    main()
