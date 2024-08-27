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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Path to chromedriver
CHROMEDRIVER_PATH = 'chromedriver.exe'

# Configure WebDriver
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

def clean_text(text):
    """Clean and normalize text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s,.]', '', text)  # Keep only words, spaces, and basic punctuation
    return text.lower().strip()

def extract_relevant_text(text):
    """Extract sentences that might mention the founder."""
    sentences = text.split('.')
    keywords = ['founder', 'co-founder', 'founder of', 'founded by']
    relevant_sentences = [s for s in sentences if any(kw in s for kw in keywords)]
    return ' '.join(relevant_sentences)

def filter_founder_names(names):
    """Filter out irrelevant names."""
    filtered_names = []
    for name in names:
        if len(name.split()) >= 2 and not re.search(r'\b(?:search|website|form|adv|llc)\b', name, re.IGNORECASE):
            filtered_names.append(name)
    return filtered_names

def extract_founder_names(text):
    """Use NER to extract potential founder names."""
    relevant_text = extract_relevant_text(text)
    doc = nlp(relevant_text)
    names = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
    return filter_founder_names(names)

def search_google(query):
    """Search Google for a query."""
    driver.get("http://www.google.com")
    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "search")))
    time.sleep(2)  # Allow time for results to load

def get_founder_name_from_wikipedia(company_name):
    """Try to find the founder on Wikipedia."""
    search_google(f"{company_name} founder site:wikipedia.org")
    try:
        first_result = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3[contains(text(),'Wikipedia')]"))
        )
        first_result.click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "firstHeading")))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = clean_text(soup.get_text())
        names = extract_founder_names(text)
        if names:
            return names[:1], "Wikipedia"
    except Exception as e:
        logging.error(f"Error during Wikipedia search: {e}")
    return ["Not found"], "Wikipedia"

def get_founder_name_from_google(company_name):
    """Try to find the founder via Google search."""
    search_google(f"{company_name} founder name")
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text = clean_text(soup.get_text())
        names = extract_founder_names(text)
        if names:
            return names[:1], "Google"
    except Exception as e:
        logging.error(f"Error during Google search: {e}")
    return ["Not found"], "Google"

def get_founder_name(company_name):
    """Get founder's name from Google, fallback to Wikipedia."""
    founder_names, source = get_founder_name_from_google(company_name)
    if "Not found" in founder_names:
        founder_names, source = get_founder_name_from_wikipedia(company_name)
    return founder_names, source

def process_companies(input_file, output_file):
    """Read input CSV, find founders, and write to output CSV."""
    with open(input_file, newline='', encoding='utf-8') as infile, open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        writer.writerow(['Company Name', 'Founder Names', 'Source'])
        for row in reader:
            company_name = row[0].strip()
            if company_name:  # Skip if company name is empty
                founder_names, source = get_founder_name(company_name)
                writer.writerow([company_name, ', '.join(founder_names), source])

if __name__ == "__main__":
    try:
        process_companies('Company_Names_Dataset.csv', 'founders.csv')
    finally:
        driver.quit()
