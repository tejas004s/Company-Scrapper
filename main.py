from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv
import spacy
import re
import logging

# Configure logging for better visibility of process flow and errors
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the spaCy NLP model for named entity recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Specify the path to the chromedriver executable
chrome_service = Service('chromedriver.exe')

# Initialize Chrome WebDriver options
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode (no GUI) for better performance
options.add_argument('--no-sandbox')  # Bypass OS security model for better stability
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems in some environments

# Create the WebDriver instance with specified service and options
driver = webdriver.Chrome(service=chrome_service, options=options)

def clean_text(text):
    """Clean and normalize text for better NER extraction."""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove unwanted punctuation and special characters
    return re.sub(r'[^\w\s,.]', '', text).strip()

def extract_relevant_text(text):
    """Extract sentences that are likely to contain the founder's name."""
    # Split the text into sentences
    sentences = text.split('.')
    # Filter sentences that mention the word "founder"
    relevant_sentences = [sentence for sentence in sentences if 'founder' in sentence.lower()]
    return ' '.join(relevant_sentences)

def filter_founder_names(names):
    """Filter out irrelevant or incomplete names."""
    filtered_names = []

    for name in names:
        # Include only names that have at least two parts (e.g., first and last name)
        if len(name.split()) >= 2:
            filtered_names.append(name)

    return filtered_names

def extract_founder_names(text):
    """Use spaCy NER to extract person names from relevant text."""
    # Extract sentences likely to contain founder's names
    relevant_text = extract_relevant_text(text)
    # Run NER on the relevant text to identify entities labeled as "PERSON"
    doc = nlp(relevant_text)
    # Extract the names from the identified entities
    names = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    return filter_founder_names(names)

def search_google(query):
    """Perform a Google search and wait for the results to load."""
    driver.get("http://www.google.com")
    search_box = driver.find_element(By.NAME, "q")  # Find the search box
    search_box.clear()  # Clear any pre-existing text in the search box
    search_box.send_keys(query)  # Type the search query
    search_box.send_keys(Keys.RETURN)  # Submit the search
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))  # Wait until search results are loaded

def get_founder_name_from_google(company_name):
    """Search for the founder's name using Google search results."""
    search_google(f"{company_name} founder name")  # Search for the company's founder name on Google
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Parse the search result page
        text = clean_text(soup.get_text())  # Clean the extracted text
        names = extract_founder_names(text)  # Extract names from the cleaned text
        if names:
            return names[:1], "Google"  # Return the first valid name found and the source
    except Exception as e:
        logging.error(f"Error during Google search: {e}")  # Log any errors during the search
    return ["Not found"], "Google"  # Return "Not found" if no name is extracted

def get_founder_name_from_wikipedia(company_name):
    """Search for the founder's name on Wikipedia using Google search."""
    search_google(f"{company_name} founder site:wikipedia.org")  # Search specifically on Wikipedia
    try:
        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Wikipedia')]"))
        )  # Wait for the Wikipedia result to appear and click on it
        first_result.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "firstHeading")))  # Wait for the Wikipedia page to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Parse the Wikipedia page
        text = clean_text(soup.get_text())  # Clean the extracted text
        names = extract_founder_names(text)  # Extract names from the cleaned text
        if names:
            return names[:1], "Wikipedia"  # Return the first valid name found and the source
    except Exception as e:
        logging.error(f"Error during Wikipedia search: {e}")  # Log any errors during the search
    return ["Not found"], "Wikipedia"  # Return "Not found" if no name is extracted

def get_founder_name(company_name):
    """Get the founder's name by first searching on Google and then on Wikipedia if needed."""
    founder_names, source = get_founder_name_from_google(company_name)  # Try getting the founder's name from Google
    if "Not found" in founder_names:
        founder_names, source = get_founder_name_from_wikipedia(company_name)  # Fallback to Wikipedia if not found on Google
    return founder_names, source

def process_companies(input_file, output_file):
    """Read company names from an input CSV, extract founders' names, and write the results to an output CSV."""
    with open(input_file, newline='', encoding='utf-8') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)  # Create a CSV reader for the input file
        writer = csv.writer(outfile)  # Create a CSV writer for the output file
        writer.writerow(['Company Name', 'Founder Names', 'Source'])  # Write the header row
        for row in reader:
            company_name = row[0]  # Extract the company name from each row
            founder_names, source = get_founder_name(company_name)  # Get the founder's name and the source
            writer.writerow([company_name, ', '.join(founder_names), source])  # Write the results to the output CSV

if __name__ == "__main__":
    try:
        process_companies('Company_Names_Dataset.csv', 'founders.csv')  # Process the companies in the input CSV
    finally:
        driver.quit()  # Ensure the WebDriver is properly closed after the process is complete
