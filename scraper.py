import os
import time
import PyPDF2
import cloudscraper
from datetime import datetime
from bs4 import BeautifulSoup
import json
import pandas as pd
import re


class Logger:
    def __init__(self, name, log_file="ijerr_scraper.log"):
        self.name = name
        self.log_file = log_file

    def _write_log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {self.name} - {level} - {message}"

        # Print to console
        print(log_entry)

        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass  # Fail silently if can't write to log file

    def info(self, message):
        self._write_log("INFO", message)

    def warning(self, message):
        self._write_log("WARNING", message)

    def error(self, message):
        self._write_log("ERROR", message)


def sanitize_filename(text, max_length=50):
    """Sanitize text for use as filename."""
    # Remove non-ASCII characters and replace with underscore
    sanitized = re.sub(r"[^\x00-\x7F]+", "_", text)
    # Replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", sanitized)
    # Remove multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized[:max_length].strip("_")


def random_delay(min_seconds=5, max_seconds=12):
    """Apply random delay between requests."""
    import random

    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


class IJERRScraper:
    """Scraper for IJERR journal articles with CSV export functionality."""

    def __init__(
        self,
        base_url="https://qtanalytics.in/journals/index.php/IJERR/home",
        max_articles=None,
    ):
        self.base_url = base_url
        self.session = cloudscraper.create_scraper()
        self.volume = "N/A"
        self.year = "N/A"
        self.articles_data = []
        self.max_articles = max_articles
        self.logger = Logger(self.__class__.__name__)

        self.logger.info(f"IJERRScraper initialized for: {self.base_url}")
        if max_articles:
            self.logger.info(f"Limiting scraping to maximum {max_articles} articles")

    def fetch_page(self, url, description="page"):
        """Fetch a web page and return its HTML content."""
        self.logger.info(f"Fetching {description}: {url}")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            self.logger.info(f"{description.capitalize()} fetched successfully")
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {description} from {url}: {str(e)}")
            return None

    def save_html(self, content, filename):
        """Save HTML content to file."""
        try:
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)
            self.logger.info(f"HTML saved to '{filename}'")
        except Exception as e:
            self.logger.error(f"Failed to save HTML to '{filename}': {str(e)}")

    def extract_volume_year(self, html_content):
        """Extract volume and year from current issue page."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            h1_element = soup.find("h1")

            if not h1_element:
                self.logger.warning("No h1 element found for volume/year extraction")
                return "N/A", "N/A"

            h1_text = h1_element.get_text(strip=True)
            self.logger.info(f"Found h1 text: '{h1_text}'")

            volume_match = re.search(r"Vol\.\s*(\d+)", h1_text, re.IGNORECASE)
            year_match = re.search(r"\((\d{4})\)", h1_text)

            volume = volume_match.group(1) if volume_match else "N/A"
            year = year_match.group(1) if year_match else "N/A"

            self.logger.info(f"Extracted - Volume: {volume}, Year: {year}")
            return volume, year

        except Exception as e:
            self.logger.error(f"Error extracting volume/year: {str(e)}")
            return "N/A", "N/A"

    def parse_article_summary(self, article_div):
        """Parse individual article summary div."""
        article = {
            "title": "N/A",
            "authors": "N/A",
            "pages": "N/A",
            "article_url": "N/A",
            "pdf_url": "N/A",
            "doi": "N/A",
            "volume": self.volume,
            "year": self.year,
        }

        # Extract title and article URL
        title_element = article_div.find("h3", class_="title")
        if title_element:
            title_link = title_element.find("a")
            if title_link:
                article["title"] = title_link.get_text(strip=True)
                article["article_url"] = title_link.get("href", "N/A")

        # Extract authors
        authors_div = article_div.find("div", class_="authors")
        if authors_div:
            article["authors"] = authors_div.get_text(strip=True)

        # Extract pages
        pages_div = article_div.find("div", class_="pages")
        if pages_div:
            article["pages"] = pages_div.get_text(strip=True)

        # Extract PDF URL
        pdf_link = article_div.find("a", class_="obj_galley_link pdf")
        if pdf_link:
            article["pdf_url"] = pdf_link.get("href", "N/A")

        return article

    def extract_doi_from_article_page(self, html_content):
        """Extract DOI from individual article page."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            doi_element = soup.select_one("section.item.doi span.value a")

            if doi_element and doi_element.get("href"):
                doi_url = doi_element["href"]
                doi_match = re.search(r"https://doi.org/(.*)", doi_url)
                if doi_match:
                    doi = doi_match.group(1)
                    self.logger.info(f"Extracted DOI: {doi}")
                    return doi

            self.logger.warning("DOI not found on article page")
            return "N/A"

        except Exception as e:
            self.logger.error(f"Error extracting DOI: {str(e)}")
            return "N/A"

    def download_pdf(self, pdf_url, doi, output_dir="pdfs"):
        """Download PDF file."""
        if pdf_url == "N/A" or doi == "N/A":
            return False

        try:
            os.makedirs(output_dir, exist_ok=True)

            # Convert view URL to download URL
            download_url = pdf_url.replace("/view/", "/download/")

            # Create safe filename
            safe_doi = sanitize_filename(doi)
            filename = f"{safe_doi}.pdf"
            filepath = os.path.join(output_dir, filename)

            self.logger.info(f"Downloading PDF: {download_url}")

            response = self.session.get(download_url, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")
            if "application/pdf" in content_type:
                with open(filepath, "wb") as pdf_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        pdf_file.write(chunk)

                self.logger.info(f"PDF downloaded: {filepath}")
                return True
            else:
                self.logger.warning(f"URL did not return PDF content: {download_url}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to download PDF: {str(e)}")
            return False

    def scrape_current_issue(self, download_pdfs=True, save_html=False):
        """Main method to scrape current issue articles."""
        self.logger.info("Starting scrape of current issue")

        # Load home page
        home_html = self.fetch_page(self.base_url, "home page")
        if not home_html:
            return []

        if save_html:
            self.save_html(home_html, "home_page.html")

        # Find current issue URL
        soup = BeautifulSoup(home_html, "html.parser")
        current_link = soup.select_one(
            'ul#navigationPrimary li a[href*="/issue/current"]'
        )

        if not current_link:
            self.logger.error("Current issue link not found")
            return []

        current_issue_url = current_link["href"]
        self.logger.info(f"Found current issue URL: {current_issue_url}")

        delay = random_delay()
        self.logger.info(f"Applied delay: {delay:.2f} seconds")

        # Load current issue page
        current_issue_html = self.fetch_page(current_issue_url, "current issue page")
        if not current_issue_html:
            return []

        if save_html:
            self.save_html(current_issue_html, "current_issue.html")

        # Extract volume and year
        self.volume, self.year = self.extract_volume_year(current_issue_html)

        # Parse articles
        soup = BeautifulSoup(current_issue_html, "html.parser")
        article_divs = soup.find_all("div", class_="obj_article_summary")

        if not article_divs:
            self.logger.warning("No articles found")
            return []

        # Apply article limit if specified
        articles_to_process = article_divs
        if self.max_articles and len(article_divs) > self.max_articles:
            articles_to_process = article_divs[: self.max_articles]
            self.logger.info(
                f"Found {len(article_divs)} articles, limiting to {self.max_articles}"
            )
        else:
            self.logger.info(f"Found {len(article_divs)} articles")

        # Process each article
        for i, article_div in enumerate(articles_to_process, 1):
            self.logger.info(f"Processing article {i}/{len(articles_to_process)}")

            article = self.parse_article_summary(article_div)

            # Get DOI from article page
            if article["article_url"] != "N/A":
                delay = random_delay()
                self.logger.info(f"Applied delay: {delay:.2f} seconds")

                article_html = self.fetch_page(
                    article["article_url"], f"article {i} page"
                )

                if article_html:
                    article["doi"] = self.extract_doi_from_article_page(article_html)

                    if save_html:
                        article_id_match = re.search(
                            r"/article/view/(\d+)", article["article_url"]
                        )
                        article_id = (
                            article_id_match.group(1)
                            if article_id_match
                            else f"article_{i}"
                        )
                        safe_title = sanitize_filename(article["title"])
                        filename = f"article_{article_id}_{safe_title}.html"
                        self.save_html(article_html, filename)

            # Download PDF if requested
            if (
                download_pdfs
                and article["pdf_url"] != "N/A"
                and article["doi"] != "N/A"
            ):
                delay = random_delay()
                self.logger.info(f"Applied delay: {delay:.2f} seconds")
                self.download_pdf(article["pdf_url"], article["doi"])

            self.articles_data.append(article)

        self.logger.info(f"Completed scraping {len(self.articles_data)} articles")
        return self.articles_data

    def save_to_csv(self, filename=None):
        """Save scraped data to CSV file."""
        if not self.articles_data:
            self.logger.warning("No data to save")
            return ""

        if filename is None:
            filename = f"IJERR_Vol{self.volume}_{self.year}_articles.csv"

        try:
            df = pd.DataFrame(self.articles_data)
            df.to_csv(filename, index=False, encoding="utf-8")
            self.logger.info(f"Data saved to CSV: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save CSV: {str(e)}")
            return ""

    def get_summary(self):
        """Get summary of scraped data."""
        return {
            "volume": self.volume,
            "year": self.year,
            "total_articles": len(self.articles_data),
            "articles_with_doi": sum(
                1 for a in self.articles_data if a["doi"] != "N/A"
            ),
            "articles_with_pdf": sum(
                1 for a in self.articles_data if a["pdf_url"] != "N/A"
            ),
        }

    def save_summary_json(self, filename=None):
        """Save summary to JSON file."""
        if filename is None:
            filename = f"IJERR_Vol{self.volume}_{self.year}_summary.json"

        try:
            summary = self.get_summary()
            summary["scrape_timestamp"] = datetime.now().isoformat()
            summary["articles"] = self.articles_data

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Summary saved to JSON: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to save JSON: {str(e)}")
            return ""

    def extract_data_from_pdf(pdf_path):
        extracted_text = ""
        try:
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                # Iterate through each page and extract text
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    extracted_text += page.extract_text()
        except FileNotFoundError:
            print(f"Error: PDF file not found at {pdf_path}")
            return []
        except Exception as e:
            print(f"An error occurred while reading the PDF: {e}")
            return []

        pattern = r"\b\d{2}-\d{2}\b"
        matches = re.findall(pattern, extracted_text)

        if matches:
            print(f"Found matches for 'XX-XX': {matches}")
        else:
            print("No 'XX-XX' pattern found in the PDF text.")

        return matches


def main():
    """Main execution function."""
    # Initialize scraper with maximum article limit
    scraper = IJERRScraper(max_articles=None)  # Limit to 5 articles for example

    # Scrape current issue
    articles = scraper.scrape_current_issue(
        download_pdfs=True,  # Set to False to skip PDF downloads
        save_html=False,  # Set to True to save HTML files
    )

    if articles:
        # Save to CSV using pandas
        csv_filename = scraper.save_to_csv()

        # Save summary as JSON
        json_filename = scraper.save_summary_json()

        # Print summary
        summary = scraper.get_summary()
        print(f"\n{'=' * 50}")
        print("SCRAPING SUMMARY")
        print(f"{'=' * 50}")
        print(f"Volume: {summary['volume']}")
        print(f"Year: {summary['year']}")
        print(f"Total Articles: {summary['total_articles']}")
        print(f"Articles with DOI: {summary['articles_with_doi']}")
        print(f"Articles with PDF: {summary['articles_with_pdf']}")
        print(f"CSV File: {csv_filename}")
        print(f"JSON File: {json_filename}")
        print(f"{'=' * 50}")
    else:
        print("No articles were scraped.")


if __name__ == "__main__":
    main()
