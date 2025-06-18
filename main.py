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

        # Enhanced CloudScraper configuration
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True},
            delay=delay,
        )

        # Add realistic headers
        self.scraper.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        self.session = self.scraper
        self.articles_data = []

    def handle_verification_challenge(self, response, url):
        """
        Handle various verification challenges
        """
        soup = BeautifulSoup(response.content, "html.parser")

        # Check for common verification indicators
        verification_indicators = [
            "captcha",
            "verification",
            "challenge",
            "human",
            "robot",
            "security check",
            "please verify",
        ]

        page_text = soup.get_text().lower()

        if any(indicator in page_text for indicator in verification_indicators):
            print(f"⚠️  Human verification detected on {url}")
            print("💡 Verification handling options:")
            print("1. Manual intervention required")
            print("2. Waiting for automatic resolution...")

            # Strategy 1: Wait and retry with longer delays
            for attempt in range(3):
                print(f"🔄 Retry attempt {attempt + 1}/3...")
                time.sleep(10 + (attempt * 5))  # Progressive delay

                retry_response = self.session.get(url)
                if self.is_verification_page(retry_response):
                    continue
                else:
                    print("✅ Verification passed automatically!")
                    return retry_response

            # Strategy 2: Manual intervention
            print("\n🚨 Manual intervention required!")
            print(f"Please open this URL in your browser: {url}")
            print("Complete the verification, then press Enter to continue...")
            input("Press Enter after completing verification...")

            # Try again after manual intervention
            return self.session.get(url)

        return response

    def is_verification_page(self, response):
        """
        Check if the response contains verification challenges
        """
        if not response:
            return True

        soup = BeautifulSoup(response.content, "html.parser")
        page_text = soup.get_text().lower()

        verification_keywords = [
            "verify you are human",
            "captcha",
            "cloudflare",
            "security check",
            "please wait",
            "checking your browser",
            "challenge",
            "robot",
            "automated",
        ]

        return any(keyword in page_text for keyword in verification_keywords)

    def get_page_with_verification_handling(self, url, max_retries=3):
        """
        Enhanced page fetching with verification handling
        """
        for attempt in range(max_retries):
            try:
                print(f"🌐 Fetching: {url} (Attempt {attempt + 1}/{max_retries})")

                # Add random delay to appear more human-like
                human_delay = self.delay + (attempt * 2)
                time.sleep(human_delay)

                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Check if we hit a verification page
                if self.is_verification_page(response):
                    print(f"🔒 Verification challenge detected (Attempt {attempt + 1})")
                    response = self.handle_verification_challenge(response, url)

                    # Verify the challenge was resolved
                    if self.is_verification_page(response):
                        if attempt < max_retries - 1:
                            print(
                                f"⏳ Verification not resolved, waiting before retry..."
                            )
                            time.sleep(30)  # Longer wait before retry
                            continue
                        else:
                            print("❌ Could not bypass verification after all attempts")
                            return None

                print("✅ Page fetched successfully")
                return response

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(15)
                    continue

            except requests.RequestException as e:
                print(f"❌ Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(10)
                    continue

        print(f"💥 Failed to fetch {url} after {max_retries} attempts")
        return None

    def get_page(self, url):
        """
        Wrapper for the enhanced page fetching
        """
        return self.get_page_with_verification_handling(url)

    def save_progress(self, filename="scraping_progress.json"):
        """
        Save current progress to resume later if needed
        """
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "articles_processed": len(self.articles_data),
            "articles_data": self.articles_data,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

        print(f"💾 Progress saved to {filename}")

    def load_progress(self, filename="scraping_progress.json"):
        """
        Load previous progress to resume scraping
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                progress_data = json.load(f)
                self.articles_data = progress_data.get("articles_data", [])
                print(f"📂 Loaded progress: {len(self.articles_data)} articles")
                return True
        except FileNotFoundError:
            print("📂 No previous progress found, starting fresh")
            return False
        except Exception as e:
            print(f"❌ Error loading progress: {e}")
            return False

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
                    print(f"📖 Found volume info: {text}")

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
            print(f"❌ Error extracting volume info: {e}")

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
            print(f"❌ Error extracting title: {e}")
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
            print(f"❌ Error extracting article URL: {e}")
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
                    return doi_text
        except Exception as e:
            print(f"❌ Error extracting DOI: {e}")
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
            print(f"❌ Error extracting PDF URL: {e}")
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
            print(f"❌ Error extracting page range: {e}")
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
            print(f"❌ Error extracting authors: {e}")
        return None

    def extract_article_tables(self, soup):
        """
        Extract all article tables from the content div
        """
        try:
            content_div = soup.find("div", {"id": "content"})
            if content_div:
                article_tables = content_div.find_all("table", class_="tocArticle")
                print(f"📊 Found {len(article_tables)} article tables")
                return article_tables
        except Exception as e:
            print(f"❌ Error extracting article tables: {e}")
        return []

    def download_pdf(self, pdf_url, filename):
        """
        Download PDF file with verification handling
        """
        try:
            print(f"📥 Downloading PDF: {filename}")
            response = self.get_page_with_verification_handling(pdf_url)

            if not response:
                return False

            # Create downloads directory if it doesn't exist
            os.makedirs("downloads", exist_ok=True)

            filepath = os.path.join("downloads", filename)
            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"✅ Downloaded: {filename}")
            return True

        except Exception as e:
            print(f"❌ Error downloading {pdf_url}: {e}")
            return False

    def create_safe_filename(self, title, year, volume, issue):
        """
        Create a safe filename for the PDF
        """
        safe_title = re.sub(r"[^\w\s-]", "", title or "untitled")[:50]
        safe_title = re.sub(r"[-\s]+", "-", safe_title).strip("-")

        filename = (
            f"{year or 'unknown'}_Vol{volume or 'x'}_No{issue or 'x'}_{safe_title}.pdf"
        )
        return filename

    def scrape_articles(self, resume=True):
        """
        Main scraping function with resume capability
        """
        print("🚀 Starting journal scraping...")
        print(f"📍 URL: {self.base_url}")
        print(f"📊 Max articles: {self.max_articles}")
        print(f"⏱️  Delay: {self.delay}s")

        # Try to resume previous progress
        if resume:
            self.load_progress()

        # Get main page
        response = self.get_page(self.base_url)
        if not response:
            print("💥 Failed to fetch main page")
            return

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract volume information
        volume_info = self.extract_volume_info(soup)
        print(f"📚 Volume info: {volume_info}")

        # Extract article tables
        article_tables = self.extract_article_tables(soup)

        if not article_tables:
            print("❌ No article tables found")
            return

        # Skip already processed articles if resuming
        start_index = len(self.articles_data)
        if start_index > 0:
            print(f"🔄 Resuming from article {start_index + 1}")

        # Limit articles if specified
        if self.max_articles > 0:
            article_tables = article_tables[: self.max_articles]
            print(f"📋 Limited to {len(article_tables)} articles")

        # Process each article
        for i, article_table in enumerate(
            article_tables[start_index:], start_index + 1
        ):
            print(f"\n📄 Processing article {i}/{len(article_tables)}")

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
                "scraped_at": datetime.now().isoformat(),
            }

            print(f"📝 Title: {article_data['title']}")
            print(f"🔗 DOI: {article_data['doi']}")
            print(f"📎 PDF URL: {article_data['pdf_url']}")
            print(f"📄 Pages: {article_data['page_range']}")
            print(f"👥 Authors: {article_data['authors']}")

            # Download PDF if available
            if article_data["pdf_url"] and article_data["title"]:
                filename = self.create_safe_filename(
                    article_data["title"],
                    article_data["year"],
                    article_data["volume"],
                    article_data["issue"],
                )

                if self.download_pdf(article_data["pdf_url"], filename):
                    article_data["download_status"] = "success"
                    article_data["local_filename"] = filename
                else:
                    article_data["download_status"] = "failed"
            else:
                article_data["download_status"] = "no_pdf_or_title"
                print("⚠️  No PDF URL or title found")

            self.articles_data.append(article_data)

            # Save progress periodically
            if i % 3 == 0:  # Save every 3 articles
                self.save_progress()
                self.save_metadata("articles_metadata_temp.csv")

            # Rate limiting with human-like variance
            delay_time = self.delay + (i % 3)  # Vary delay slightly
            print(f"⏳ Waiting {delay_time}s...")
            time.sleep(delay_time)

    def save_metadata(self, filename="articles_metadata.csv"):
        """
        Save extracted metadata to CSV
        """
        if not self.articles_data:
            print("❌ No data to save")
            return

        try:
            df = pd.DataFrame(self.articles_data)
            df.to_csv(filename, index=False, encoding="utf-8")
            print(f"💾 Metadata saved to {filename}")

            # Also save as JSON for backup
            json_filename = filename.replace(".csv", ".json")
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(self.articles_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Metadata also saved to {json_filename}")

        except Exception as e:
            print(f"❌ Error saving metadata: {e}")


# Usage example
if __name__ == "__main__":
    # Configuration
    base_url = "https://jurnal.ar-raniry.ac.id/index.php/samarah/issue/view/1249"
    max_articles = 2  # 0 means no limit, scrape all articles
    delay = 3  # Increased delay to be more respectful

    print("📋 Journal Scraper with Human Verification Support")
    print("=" * 50)

    # Create scraper instance
    scraper = JournalScraper(base_url, max_articles, delay)

    try:
        # Run scraping with resume capability
        scraper.scrape_articles(resume=True)

        # Save final metadata
        scraper.save_metadata()

        print("\n🎉 Scraping completed!")
        print(f"📊 Total articles processed: {len(scraper.articles_data)}")

        # Print summary
        successful_downloads = sum(
            1
            for article in scraper.articles_data
            if article["download_status"] == "success"
        )
        print(f"✅ Successful downloads: {successful_downloads}")

        # Print first article details for verification
        if scraper.articles_data:
            print("\n📄 First article details:")
            first_article = scraper.articles_data[0]
            for key, value in first_article.items():
                print(f"  {key}: {value}")

    except KeyboardInterrupt:
        print("\n⏹️  Scraping interrupted by user")
        scraper.save_progress()
        scraper.save_metadata("articles_metadata_partial.csv")
        print("💾 Progress saved for later resumption")

    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        scraper.save_progress()
        scraper.save_metadata("articles_metadata_error.csv")
        print("💾 Progress saved despite error")
