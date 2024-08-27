# Import necessary libraries for Selenium and web scraping
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
import time

# Set up logging to track the script's activity
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load spaCy model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Path to the ChromeDriver executable
CHROMEDRIVER_PATH = 'chromedriver.exe'

# Configure WebDriver options for Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run Chrome in headless mode (without a GUI)
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Initialize WebDriver with the specified options
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

def clean_text(text):
    """Clean and normalize text by removing unnecessary characters and whitespace."""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = re.sub(r'[^\w\s,.]', '', text)  # Keep only words, spaces, and basic punctuation
    return text.lower().strip()  # Convert text to lowercase and remove leading/trailing whitespace

def extract_relevant_text(text):
    """Extract sentences that are likely to mention the founder from the given text."""
    sentences = text.split('.')  # Split text into sentences
    keywords = ['founder', 'co-founder', 'founder of', 'founded by']  # Keywords to identify relevant sentences
    relevant_sentences = [s for s in sentences if any(kw in s for kw in keywords)]  # Filter sentences containing keywords
    return ' '.join(relevant_sentences)  # Join relevant sentences into a single string

def filter_founder_names(names):
    """Filter out irrelevant names based on certain criteria."""
    filtered_names = []
    for name in names:
        if len(name.split()) >= 2 and not re.search(r'\b(?:search|website|form|adv|llc)\b', name, re.IGNORECASE):
            filtered_names.append(name)  # Keep names with at least two words and no unwanted keywords
    return filtered_names

def extract_founder_names(text):
    """Use spaCy's NER to extract potential founder names from the relevant text."""
    relevant_text = extract_relevant_text(text)
    doc = nlp(relevant_text)  # Apply NER to the relevant text
    names = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]  # Extract entities labeled as PERSON
    return filter_founder_names(names)  # Filter out irrelevant names

def search_google(query):
    """Search Google for the specified query."""
    driver.get("http://www.google.com")  # Open Google in the browser
    search_box = driver.find_element(By.NAME, "q")  # Find the search box element
    search_box.clear()  # Clear any existing text in the search box
    search_box.send_keys(query)  # Enter the search query
    search_box.send_keys(Keys.RETURN)  # Submit the search form
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))  # Wait for the search results to load
    time.sleep(2)  # Allow additional time for results to fully load

def get_founder_name_from_wikipedia(company_name):
    """Try to find the founder's name on Wikipedia using Google search."""
    search_google(f"{company_name} founder site:wikipedia.org")  # Search for the company's founder on Wikipedia
    try:
        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Wikipedia')]"))
        )  # Wait for a Wikipedia result to appear and select it
        first_result.click()  # Click on the first Wikipedia result
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "firstHeading")))  # Wait for the Wikipedia page to load
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Parse the page source with BeautifulSoup
        text = clean_text(soup.get_text())  # Clean the text content of the page
        names = extract_founder_names(text)  # Extract founder names using NER
        if names:
            return names[:1], "Wikipedia"  # Return the first found name and the source
    except Exception as e:
        logging.error(f"Error during Wikipedia search: {e}")  # Log any errors encountered
    return ["Not found"], "Wikipedia"  # Return "Not found" if no names are extracted

def get_founder_name_from_google(company_name):
    """Try to find the founder's name directly via Google search."""
    search_google(f"{company_name} founder name")  # Search for the company's founder on Google
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Parse the page source with BeautifulSoup
        text = clean_text(soup.get_text())  # Clean the text content of the page
        names = extract_founder_names(text)  # Extract founder names using NER
        if names:
            return names[:1], "Google"  # Return the first found name and the source
    except Exception as e:
        logging.error(f"Error during Google search: {e}")  # Log any errors encountered
    return ["Not found"], "Google"  # Return "Not found" if no names are extracted

def get_founder_name(company_name):
    """Attempt to retrieve the founder's name, using Google first, then Wikipedia as a fallback."""
    founder_names, source = get_founder_name_from_google(company_name)  # Try Google search first
    if "Not found" in founder_names:
        founder_names, source = get_founder_name_from_wikipedia(company_name)  # Fallback to Wikipedia if Google fails
    return founder_names, source  # Return the found names and their source

def process_companies(input_file, output_file):
    """Process a list of company names from a CSV file to find and write their founders' names to an output CSV."""
    with open(input_file, newline='', encoding='utf-8') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        writer.writerow(['Company Name', 'Founder Names', 'Source'])  # Write header row to output CSV
        for row in reader:
            company_name = row[0].strip()  # Read and clean each company name
            if company_name:  # Skip if company name is empty
                founder_names, source = get_founder_name(company_name)  # Get the founder names and source
                writer.writerow([company_name, ', '.join(founder_names), source])  # Write the results to the output CSV

if __name__ == "__main__":
    try:
        process_companies('Company_Names_Dataset.csv', 'founders.csv')  # Start the process of finding founder names
    finally:
        driver.quit()  # Ensure the WebDriver is properly closed after execution
