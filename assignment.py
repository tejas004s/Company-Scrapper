import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import csv


# Load company names from CSV
def load_company_names(csv_file):
    return pd.read_csv(csv_file)['Company Name'].tolist()


# Fetch founder info using Crunchbase API
def fetch_founder_from_api(company_name, api_key):
    try:
        url = f"https://api.crunchbase.com/api/v4/entities/organizations/{company_name.lower()}?user_key={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            founders = [item['name'] for item in data.get('founders', [])]
            return '; '.join(founders) if founders else None
        else:
            print(f"API request failed for {company_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching data from API for {company_name}: {e}")
        return None


# Web scraping logic to find the founder's name (example using Wikipedia)
def scrape_founder_from_web(company_name):
    try:
        search_url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
        response = requests.get(search_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            infobox = soup.find('table', {'class': 'infobox vcard'})
            if infobox:
                for row in infobox.find_all('tr'):
                    if 'Founder' in row.text:
                        founder_names = row.find('td').text.strip()
                        return founder_names.replace('\n', '; ')
        return None
    except Exception as e:
        print(f"An error occurred while scraping the web for {company_name}: {e}")
        return None


# Save results to CSV
def save_results_to_csv(results, output_file):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Company Name', 'Founder(s)'])
        writer.writerows(results)


# Main script
def main():
    companies = load_company_names('data.csv')
    api_key = 'fd4a9f709252960d4797df5921143a1f'  # Replace with your actual API key
    results = []

    for company in companies:
        print(f"Processing {company}...")
        founder = fetch_founder_from_api(company, api_key)

        if not founder:
            print(f"API failed or returned no data for {company}. Attempting to scrape...")
            founder = scrape_founder_from_web(company)

        if founder:
            print(f"Founder of {company}: {founder}")
        else:
            print(f"Founder information for {company} not found.")
            founder = "Not Found"

        results.append([company, founder])

        # To avoid getting blocked by too many requests
        time.sleep(1)

    # Save results to a new CSV file
    save_results_to_csv(results, 'founders_results.csv')
    print("Results saved to 'founders_results.csv'.")


if __name__ == "__main__":
    main()

