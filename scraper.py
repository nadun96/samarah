import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import os
from lxml import html
import re
import unicodedata
import time  # Import the time module
import random  # Import the random module


class IJERRScraper:
    def __init__(self, base_url="https://qtanalytics.in/journals/index.php/IJERR/home"):
        self.base_url = base_url
        self.scraper = cloudscraper.create_scraper()
        self.home_page_html = None
        self.current_issue_html = None
        self.sleep_min = 2  # Minimum sleep duration in seconds
        self.sleep_max = 5  # Maximum sleep duration in seconds
        print(f"IJERRScraper initialized for base URL: {self.base_url}")

    def _apply_random_delay(self):
        delay = random.uniform(self.sleep_min, self.sleep_max)
        print(f"Pausing for {delay:.2f} seconds to simulate human behavior...")
        time.sleep(delay)

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

    def _save_content(self, content, filename):
        if content:
            try:
                content_to_write = str(content)
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(content_to_write)
                print(f"Content saved to '{filename}'")
            except Exception as e:
                print(f"Error saving content to '{filename}': {e}")
        else:
            print(f"No content to save for '{filename}'.")

    def load_home_page(self, save_html=True, filename="IJERR_homepage.html"):
        self.home_page_html = self._make_request(self.base_url, "home page")
        if save_html and self.home_page_html:
            self._save_content(self.home_page_html, filename)
        self._apply_random_delay()
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
                self._save_content(self.current_issue_html, filename)
            self._apply_random_delay()
            return self.current_issue_html
        return None

    def extract_volume_and_year(self) -> tuple[str, str]:
        if not self.current_issue_html:
            print("Current issue HTML not loaded. Cannot extract volume and year.")
            return "N/A", "N/A"

        try:
            tree = html.fromstring(self.current_issue_html)
            h1_elements = tree.xpath("/html/body/div/div[1]/div[1]/div/h1")
            if h1_elements:
                h1_text = h1_elements[0].text_content().strip()
                print(f"Found h1 text: '{h1_text}'")

                volume_match = re.search(r"Vol\.\s*(\d+)", h1_text, re.IGNORECASE)
                year_match = re.search(r"\((\d{4})\)", h1_text)

                volume = volume_match.group(1) if volume_match else "N/A"
                year = year_match.group(1) if year_match else "N/A"

                return volume, year
            else:
                print("No <h1> element found at the specified XPath.")
                return "N/A", "N/A"
        except Exception as e:
            print(f"An error occurred during volume and year extraction: {e}")
            return "N/A", "N/A"

    def parse_current_issue_articles(self) -> list[dict]:
        if not self.current_issue_html:
            print(
                "Current issue HTML not loaded. Please call load_current_issue_page() first."
            )
            return []

        soup = BeautifulSoup(self.current_issue_html, "html.parser")
        articles_data = []

        article_summary_divs = soup.find_all("div", class_="obj_article_summary")

        if not article_summary_divs:
            print("No article summary divs found on the current issue page.")
            return []

        print(f"Found {len(article_summary_divs)} article summaries.")

        for article_div in article_summary_divs:
            article = {}

            title_link_element = article_div.find("h3", class_="title").find("a")
            article["title"] = (
                title_link_element.get_text(strip=True) if title_link_element else "N/A"
            )
            article["article_url"] = (
                title_link_element["href"]
                if title_link_element and "href" in title_link_element.attrs
                else "N/A"
            )

            authors_div = article_div.find("div", class_="authors")
            article["authors"] = (
                authors_div.get_text(strip=True) if authors_div else "N/A"
            )

            pages_div = article_div.find("div", class_="pages")
            article["pages"] = pages_div.get_text(strip=True) if pages_div else "N/A"

            pdf_link = article_div.find("a", class_="obj_galley_link pdf")
            article["pdf_url"] = (
                pdf_link["href"] if pdf_link and "href" in pdf_link.attrs else "N/A"
            )

            check_for_updates_link = article_div.find(
                "a", class_="obj_galley_link file"
            )
            article["check_for_updates_url"] = (
                check_for_updates_link["href"]
                if check_for_updates_link and "href" in check_for_updates_link.attrs
                else "N/A"
            )

            articles_data.append(article)

        return articles_data

    def download_article_page(self, article_data: dict, output_dir="articles_html"):
        if not "article_url" in article_data or not article_data["article_url"]:
            print("Article data missing 'article_url'. Cannot download page.")
            return False, None

        article_url = article_data["article_url"]
        article_title_for_log = article_data.get("title", "untitled_article")

        filename_base = (
            unicodedata.normalize("NFKD", article_title_for_log)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )
        filename_base = re.sub(r"[^a-zA-Z0-9_\-.]", "", filename_base)
        filename_base = filename_base[:50].strip()

        article_id_match = re.search(r"/article/view/(\d+)", article_url)
        article_id = article_id_match.group(1) if article_id_match else "unknown_id"

        final_filename = f"article_{article_id}_{filename_base}.html"
        full_path = os.path.join(output_dir, final_filename)

        os.makedirs(output_dir, exist_ok=True)

        article_html = self._make_request(
            article_url, f"article page '{article_title_for_log}'"
        )
        if article_html:
            self._save_content(article_html, full_path)
            self._apply_random_delay()  # Apply delay after each article page download
            return True, article_html
        return False, None

    def extract_article_title_from_page(self, article_page_html: str) -> str:
        if not article_page_html:
            print("No HTML content provided to extract article title.")
            return "N/A"

        try:
            soup = BeautifulSoup(article_page_html, "html.parser")
            title_h1 = soup.find("h1", class_="page_title")

            if title_h1:
                title = title_h1.get_text(strip=True)
                print(f"Extracted article title from page: '{title}'")
                return title
            else:
                print("No <h1 class='page_title'> element found on the article page.")
                return "N/A"
        except Exception as e:
            print(f"An error occurred during article title extraction: {e}")
            return "N/A"

    def extract_doi_from_page(self, article_page_html: str) -> str:
        if not article_page_html:
            print("No HTML content provided to extract DOI.")
            return "N/A"

        try:
            soup = BeautifulSoup(article_page_html, "html.parser")
            doi_link_element = soup.select_one("section.item.doi span.value a")

            if doi_link_element and "href" in doi_link_element.attrs:
                full_doi_url = doi_link_element["href"]
                doi_match = re.search(r"https://doi.org/(.*)", full_doi_url)
                if doi_match:
                    doi = doi_match.group(1)
                    print(f"Extracted DOI: '{doi}'")
                    return doi
                else:
                    print(f"DOI URL format not as expected: {full_doi_url}")
                    return "N/A"
            else:
                print("DOI link element not found on the article page.")
                return "N/A"
        except Exception as e:
            print(f"An error occurred during DOI extraction: {e}")
            return "N/A"


if __name__ == "__main__":
    scraper = IJERRScraper()

    home_html = scraper.load_home_page()

    if home_html:
        current_issue_html = scraper.load_current_issue_page()

        if current_issue_html:
            volume, year = scraper.extract_volume_and_year()
            if volume and year:
                print(f"Current Issue Details: Volume {volume}, Year {year}")
            else:
                print("Could not extract current volume and year.")

            articles = scraper.parse_current_issue_articles()
            print(f"\nNumber of articles found: {len(articles)}")

            for i, article in enumerate(articles):
                if i > 2:  # Limit to first 3 articles for demonstration
                    break
                print(
                    f"\nAttempting to download Article {i + 1}: {article.get('title', 'N/A')}"
                )
                download_success, article_page_html = scraper.download_article_page(
                    article
                )

                if download_success:
                    print(f"Successfully downloaded article {i + 1} page.")

                    # Extract title from the downloaded page's HTML
                    extracted_title = scraper.extract_article_title_from_page(
                        article_page_html
                    )
                    if extracted_title != "N/A":
                        print(f"  Confirmed Title: {extracted_title}")

                    # Extract DOI from the downloaded article page
                    extracted_doi = scraper.extract_doi_from_page(article_page_html)
                    if extracted_doi != "N/A":
                        print(f"  Extracted DOI: {extracted_doi}")

                else:
                    print(f"Failed to download article {i + 1} page.")

        else:
            print("Failed to load current issue page.")
    else:
        print("Failed to load home page.")

    print("\nScraping process complete.")
