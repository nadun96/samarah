import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import os


class IJERRScraper:
    def __init__(self, base_url="https://qtanalytics.in/journals/index.php/IJERR/home"):
        self.base_url = base_url
        self.scraper = cloudscraper.create_scraper()
        self.home_page_html = None
        self.current_issue_html = None
        print(f"IJERRScraper initialized for base URL: {self.base_url}")

    def _make_request(self, url, description="page"):
        print(f"Attempting to load {description}: {url}")
        try:
            response = self.scraper.get(url)
            response.raise_for_status()
            print(f"{description.capitalize()} loaded successfully.")
            return response.text
        except Exception as e:
            print(f"An error occurred while loading {description} from {url}: {e}")
            return None

    def _save_html(self, html_content, filename):
        if html_content:
            try:
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(html_content)
                print(f"HTML content saved to '{filename}'")
            except Exception as e:
                print(f"Error saving HTML to '{filename}': {e}")
        else:
            print(f"No HTML content to save for '{filename}'.")

    def load_home_page(self, save_html=True, filename="IJERR_homepage.html"):
        self.home_page_html = self._make_request(self.base_url, "home page")
        if save_html and self.home_page_html:
            self._save_html(self.home_page_html, filename)
        return self.home_page_html

    def get_current_issue_url(self):
        if not self.home_page_html:
            print("Home page HTML not loaded. Please call load_home_page() first.")
            return None

        soup = BeautifulSoup(self.home_page_html, "html.parser")
        current_link_element = soup.select_one(
            'ul#navigationPrimary li a[href*="/issue/current"]'
        )

        if current_link_element:
            current_issue_url = current_link_element["href"]
            print(f"Found 'Current' issue link: {current_issue_url}")
            return current_issue_url
        else:
            print("Could not find the 'Current' issue link on the home page.")
            return None

    def load_current_issue_page(
        self, save_html=True, filename="IJERR_current_issue.html"
    ):
        current_issue_url = self.get_current_issue_url()
        if current_issue_url:
            self.current_issue_html = self._make_request(
                current_issue_url, "Current issue page"
            )
            if save_html and self.current_issue_html:
                self._save_html(self.current_issue_html, filename)
            return self.current_issue_html
        return None

    def parse_current_issue_articles(self):
        if not self.current_issue_html:
            print(
                "Current issue HTML not loaded. Please call load_current_issue_page() first."
            )
            return []

        soup = BeautifulSoup(self.current_issue_html, "html.parser")
        articles = []

        print("Parsing current issue articles (placeholder function).")
        return articles


if __name__ == "__main__":
    scraper = IJERRScraper()

    home_html = scraper.load_home_page()

    if home_html:
        current_issue_html = scraper.load_current_issue_page()

        if current_issue_html:
            pass
        else:
            print("Failed to load current issue page.")
    else:
        print("Failed to load home page.")

    print("\nScraping process complete.")
