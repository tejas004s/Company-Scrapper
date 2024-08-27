Founder Name Scraper

This Python script is designed to automate the extraction of founder names for a list of companies by scraping information from Google and Wikipedia. The script uses Selenium for web automation and spaCy for Named Entity Recognition (NER) to identify and extract founder names from the text.

Script Usage Instructions

Prerequisites

- Python 3.11 or later
- Google Chrome and ChromeDriver (compatible version with your Chrome browser)
  You can check out this website for newer versions 'https://googlechromelabs.github.io/chrome-for-testing/'
- Required Python libraries:
  - `selenium`
  - `beautifulsoup4`
  - `spacy`
  - `csv`
  - `re`
  - `logging`

Installation

1. Install the required Python libraries:
   ```bash
   pip install selenium beautifulsoup4 spacy
   ```

2. Download the spaCy English model:
   ```bash
   python -m spacy download en_core_web_md
   ```

3. Download and set up ChromeDriver:
   - Ensure that `chromedriver.exe` is placed in your script's directory or added to your system's PATH.(make sure its compatible with your chrome version eg: mine was 128.'

### Running the Script

1. Prepare the input CSV file:
   - Create a CSV file named `data.csv` containing a list of company names in the first column.
   - In this project i use 'Company_Names_dataset.csv' file consisting of more than 10,000 company names

2. Run the script:
   ```bash
   python founder_name_scraper.py
   ```

   The script will process the `Company_Name_dataset.csv` file and generate an `founders.csv` output file with the following columns:
   - `Company Name`: Name of the company.
   - `Founder Names`: Extracted founder names.
   - `Source`: Source from which the founder names were obtained (Google or Wikipedia).

Example Output

The `founders.csv` file will look like:

| Company Name | Founder Names       | Source   |

| Disney Inc. | Tom , Jerry  | Wikipedia|

| Acme Corp.   | Alice Johnson        | Google   |

 Resources Used

- Selenium: For web automation and interaction with Google and Wikipedia pages.
- BeautifulSoup: For parsing and extracting text from HTML pages.
- spaCy: For Named Entity Recognition (NER) to identify and extract human names.
- I used a medium model en_core_web_md for training you could use a large en_core_web_lg or transformer model en_core_web_trf for better results.
- ChromeDriver: WebDriver for controlling Google Chrome.

Challenges Faced

- Handling dynamic content loading: Ensuring that the entire webpage content is loaded before attempting to extract text. This was managed using Selenium's `WebDriverWait`.
- Noise in extracted text: Filtering out irrelevant text and focusing on sentences that likely contain founder names.
- Accuracy of NER: The spaCy model sometimes extracts irrelevant entities as names, requiring further filtering to improve accuracy.
- Error handling: Ensuring the script gracefully handles errors, such as network issues or missing elements on the page.

Future Improvements

- Model doesn't necessarily work for more than one founder because of NER, it detects too many irrelevant people hence keyword is restricted.
- Enhancing NER accuracy: Fine-tuning the NER model or adding custom rules to improve the accuracy of founder name extraction.
- Parallel processing: Implementing multi-threading or asynchronous processing to speed up the scraping process for large datasets.
  side-note: Although parallel processing speeds up the script it comes at a cost of computer cpu resources, which my cpu couldn't handle so if you have larger computer cpu resource try this.
- Integration with other sources: Expanding the script to include additional sources beyond Google and Wikipedia for a more comprehensive search.
- Improving text filtering: Refining the text extraction logic to reduce noise and improve the precision of the extracted sentences.


