import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import os  # Import the os module to handle file paths

# Initialize cloudscraper
scraper = cloudscraper.create_scraper()

# The URL to load
url = "https://qtanalytics.in/journals/index.php/IJERR/home"

# Define the filename for the saved HTML
html_filename = "IJERR_homepage.html"

print(f"Attempting to load: {url}")

try:
    # Load the page using cloudscraper
    response = scraper.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

    print("Page loaded successfully.")
    soup = BeautifulSoup(response.text, "html.parser")

    # Save the HTML content to a file
    with open(html_filename, "w", encoding="utf-8") as file:
        file.write(response.text)
    print(f"HTML content saved to '{html_filename}'")

    # You can also pretty-print the HTML (formatted for readability) if desired
    # with open("IJERR_homepage_pretty.html", "w", encoding="utf-8") as file:
    #     file.write(soup.prettify())
    # print(f"Pretty-printed HTML content saved to 'IJERR_homepage_pretty.html'")

    # Example: Print the title of the page to confirm it loaded correctly
    print(f"Page Title: {soup.title.string}")

except Exception as e:
    print(f"An error occurred: {e}")
