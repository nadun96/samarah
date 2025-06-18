import os
import csv
import time
import requests
import cloudscraper
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import json
import pandas as pd
import re


class JournalScraper:
    def __init__(self, base_url, max_articles=10, delay=2):
        """
        Initialize the scraper with CloudScraper to bypass Cloudflare
        """
        self.base_url = base_url
        self.max_articles = max_articles
        self.delay = delay
        self.scraper = cloudscraper.create_scraper()
        self.session = self.scraper
        self.articles_data = []

    def get_page(self, url):
        """
        Fetch a page using CloudScraper with error handling
        """
        try:
            response = self.session.get(url)
            response.raise_for_status()
            time.sleep(self.delay)  # Rate limiting
            return response
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_volume_info(self, soup):
        """
        Extract volume, issue, and year information from breadcrumb
        """
        volume_info = {"year": None, "volume": None, "issue": None}

        try:
            # Find breadcrumb div
            breadcrumb = soup.find("div", {"id": "breadcrumb"})
            if breadcrumb:
                # Look for the anchor tag with volume info
                current_link = breadcrumb.find("a", class_="current")
                if current_link:
                    text = current_link.get_text().strip()
                    print(f"Found volume info: {text}")

                    # Extract volume and issue using regex
                    vol_match = re.search(r"Vol\s*(\d+)", text, re.IGNORECASE)
                    no_match = re.search(r"No\s*(\d+)", text, re.IGNORECASE)
                    year_match = re.search(r"\((\d{4})\)", text)

                    if vol_match:
                        volume_info["volume"] = vol_match.group(1)
                    if no_match:
                        volume_info["issue"] = no_match.group(1)
                    if year_match:
                        volume_info["year"] = year_match.group(1)

        except Exception as e:
            print(f"Error extracting volume info: {e}")

        return volume_info

    def extract_article_title(self, article_table):
        """
        Extract article title from table
        """
        try:
            title_div = article_table.find("div", class_="tocTitle")
            if title_div:
                title_link = title_div.find("a")
                if title_link:
                    return title_link.get_text().strip()
        except Exception as e:
            print(f"Error extracting title: {e}")
        return None

    def extract_article_url(self, article_table):
        """
        Extract article URL from table
        """
        try:
            title_div = article_table.find("div", class_="tocTitle")
            if title_div:
                title_link = title_div.find("a")
                if title_link and title_link.get("href"):
                    return title_link["href"]
        except Exception as e:
            print(f"Error extracting article URL: {e}")
        return None

    def extract_doi(self, article_table):
        """
        Extract DOI from table
        """
        try:
            doi_div = article_table.find("div", class_="tocDOI")
            if doi_div:
                doi_link = doi_div.find("a")
                if doi_link:
                    doi_text = doi_link.get_text().strip()
                    # Clean up DOI - remove any extra whitespace or formatting
                    return doi_text
        except Exception as e:
            print(f"Error extracting DOI: {e}")
        return None

    def extract_pdf_url(self, article_table):
        """
        Extract PDF URL from table
        """
        try:
            galleys_div = article_table.find("div", class_="tocGalleys")
            if galleys_div:
                pdf_link = galleys_div.find("a", class_="file")
                if pdf_link and pdf_link.get("href"):
                    return pdf_link["href"]
        except Exception as e:
            print(f"Error extracting PDF URL: {e}")
        return None

    def extract_page_range(self, article_table):
        """
        Extract page range from table
        """
        try:
            pages_div = article_table.find("div", class_="tocPages")
            if pages_div:
                return pages_div.get_text().strip()
        except Exception as e:
            print(f"Error extracting page range: {e}")
        return None

    def extract_authors(self, article_table):
        """
        Extract authors from table
        """
        try:
            authors_div = article_table.find("div", class_="tocAuthors")
            if authors_div:
                return authors_div.get_text().strip()
        except Exception as e:
            print(f"Error extracting authors: {e}")
        return None

    def extract_article_tables(self, soup):
        """
        Extract all article tables from the content div
        """
        try:
            content_div = soup.find("div", {"id": "content"})
            if content_div:
                # Find all tables with class 'tocArticle'
                article_tables = content_div.find_all("table", class_="tocArticle")
                print(f"Found {len(article_tables)} article tables")
                return article_tables
        except Exception as e:
            print(f"Error extracting article tables: {e}")
        return []

    def download_pdf(self, pdf_url, filename):
        """
        Download PDF file
        """
        try:
            response = self.session.get(pdf_url)
            response.raise_for_status()

            # Create downloads directory if it doesn't exist
            os.makedirs("downloads", exist_ok=True)

            filepath = os.path.join("downloads", filename)
            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"Downloaded: {filename}")
            return True

        except Exception as e:
            print(f"Error downloading {pdf_url}: {e}")
            return False

    def create_safe_filename(self, title, year, volume, issue):
        """
        Create a safe filename for the PDF
        """
        # Remove invalid characters and limit length
        safe_title = re.sub(r"[^\w\s-]", "", title or "untitled")[:50]
        safe_title = re.sub(r"[-\s]+", "-", safe_title).strip("-")

        filename = (
            f"{year or 'unknown'}_Vol{volume or 'x'}_No{issue or 'x'}_{safe_title}.pdf"
        )
        return filename

    def scrape_articles(self):
        """
        Main scraping function
        """
        print(f"Starting scrape of {self.base_url}")
        print(f"Max articles: {self.max_articles}")
        print(f"Delay between requests: {self.delay}s")

        # Get main page
        response = self.get_page(self.base_url)
        if not response:
            print("Failed to fetch main page")
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract volume information
        volume_info = self.extract_volume_info(soup)
        print(f"Volume info: {volume_info}")

        # Extract article tables
        article_tables = self.extract_article_tables(soup)

        if not article_tables:
            print("No article tables found")
            return

        # Limit articles if specified
        if self.max_articles > 0:
            article_tables = article_tables[: self.max_articles]
            print(f"Limited to {len(article_tables)} articles")

        # Process each article
        for i, article_table in enumerate(article_tables, 1):
            print(f"\nProcessing article {i}/{len(article_tables)}")

            # Extract all article data
            article_data = {
                "year": volume_info["year"],
                "volume": volume_info["volume"],
                "issue": volume_info["issue"],
                "title": self.extract_article_title(article_table),
                "article_url": self.extract_article_url(article_table),
                "doi": self.extract_doi(article_table),
                "pdf_url": self.extract_pdf_url(article_table),
                "page_range": self.extract_page_range(article_table),
                "authors": self.extract_authors(article_table),
                "download_status": "pending",
                "local_filename": None,
            }

            print(f"Title: {article_data['title']}")
            print(f"DOI: {article_data['doi']}")
            print(f"PDF URL: {article_data['pdf_url']}")
            print(f"Page Range: {article_data['page_range']}")
            print(f"Authors: {article_data['authors']}")

            # Download PDF if available
            if article_data["pdf_url"] and article_data["title"]:
                filename = self.create_safe_filename(
                    article_data["title"],
                    article_data["year"],
                    article_data["volume"],
                    article_data["issue"],
                )

                print(f"Attempting to download: {filename}")
                if self.download_pdf(article_data["pdf_url"], filename):
                    article_data["download_status"] = "success"
                    article_data["local_filename"] = filename
                else:
                    article_data["download_status"] = "failed"
            else:
                article_data["download_status"] = "no_pdf_or_title"
                print("No PDF URL or title found")

            self.articles_data.append(article_data)

            # Rate limiting
            time.sleep(self.delay)

    def save_metadata(self, filename="articles_metadata.csv"):
        """
        Save extracted metadata to CSV
        """
        if not self.articles_data:
            print("No data to save")
            return

        df = pd.DataFrame(self.articles_data)
        df.to_csv(filename, index=False)
        print(f"Metadata saved to {filename}")

        # Also save as JSON for backup
        json_filename = filename.replace(".csv", ".json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(self.articles_data, f, indent=2, ensure_ascii=False)
        print(f"Metadata also saved to {json_filename}")


# Usage example
if __name__ == "__main__":
    # Configuration
    base_url = "https://jurnal.ar-raniry.ac.id/index.php/samarah/issue/view/1249"
    max_articles = 2  # 0 means no limit, scrape all articles
    delay = 2  # Seconds between requests

    # Create scraper instance
    scraper = JournalScraper(base_url, max_articles, delay)

    # Run scraping
    scraper.scrape_articles()

    # Save metadata
    scraper.save_metadata()

    print("\nScraping completed!")
    print(f"Total articles processed: {len(scraper.articles_data)}")

    # Print summary
    successful_downloads = sum(
        1
        for article in scraper.articles_data
        if article["download_status"] == "success"
    )
    print(f"Successful downloads: {successful_downloads}")

    # Print first few articles for verification
    if scraper.articles_data:
        print("\nFirst article details:")
        first_article = scraper.articles_data[0]
        for key, value in first_article.items():
            print(f"  {key}: {value}")
