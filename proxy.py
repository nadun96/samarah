import cloudscraper
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import time
import random
import itertools
from urllib.parse import urlparse
import urllib3
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings for proxy connections
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Step 1: Get Current Issue page
BASE_URL = "https://jurnal.ar-raniry.ac.id"
INDEX_URL = f"{BASE_URL}/index.php/samarah/index"

# Proxy configuration
PROXY_LIST = [
    # Free proxy examples (replace with your own working proxies)
    # Format: 'protocol://ip:port' or 'protocol://username:password@ip:port'
    "http://171.237.108.29:1010",
    "http://4.245.123.244:80",
    "http://190.58.248.86:80",
    "http://59.53.80.122:10024",
    "http://38.28.222.76:80",
    "http://38.28.222.71:80",
    # Add more proxies here
    # You can also load from file or API
]

# For testing without proxies, set this to True
USE_PROXIES = True  # Set to True when you have working proxies


class ProxyRotator:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list
        self.proxy_cycle = itertools.cycle(proxy_list) if proxy_list else None
        self.current_proxy = None
        self.failed_proxies = set()

    def get_next_proxy(self):
        if not self.proxy_cycle:
            return None

        # Try to get a working proxy
        attempts = 0
        max_attempts = len(self.proxy_list) * 2

        while attempts < max_attempts:
            proxy = next(self.proxy_cycle)
            if proxy not in self.failed_proxies:
                self.current_proxy = proxy
                return proxy
            attempts += 1

        # If all proxies failed, reset failed list and try again
        if self.failed_proxies:
            print("[!] All proxies failed, resetting failed proxy list")
            self.failed_proxies.clear()
            self.current_proxy = next(self.proxy_cycle)
            return self.current_proxy

        return None

    def mark_proxy_failed(self, proxy):
        if proxy:
            self.failed_proxies.add(proxy)
            print(f"[!] Marked proxy as failed: {proxy}")

    def get_proxy_dict(self, proxy_url):
        if not proxy_url:
            return None

        parsed = urlparse(proxy_url)
        return {"http": proxy_url, "https": proxy_url}


# Initialize proxy rotator
proxy_rotator = ProxyRotator(PROXY_LIST if USE_PROXIES else [])


def create_scraper_session(proxy_url=None):
    """Create a new CloudScraper session with optional proxy"""
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    # Configure SSL settings for proxy compatibility
    scraper.verify = False  # Disable SSL verification

    # Set up retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    scraper.mount("http://", adapter)
    scraper.mount("https://", adapter)

    if proxy_url and USE_PROXIES:
        proxy_dict = proxy_rotator.get_proxy_dict(proxy_url)
        scraper.proxies.update(proxy_dict)
        print(f"[*] Using proxy: {proxy_url}")

    return scraper


def make_request_with_retry(url, max_retries=3):
    """Make HTTP request with proxy rotation and retry logic"""
    for attempt in range(max_retries):
        current_proxy = None

        if USE_PROXIES:
            current_proxy = proxy_rotator.get_next_proxy()
            if not current_proxy:
                print("[!] No working proxies available")
                return None

        scraper = create_scraper_session(current_proxy)

        try:
            print(f"[*] Attempt {attempt + 1} - Making request to: {url}")
            if current_proxy:
                print(f"[*] Using proxy: {current_proxy}")

            # Add random user agent rotation
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            ]
            scraper.headers.update({"User-Agent": random.choice(user_agents)})

            response = scraper.get(url, timeout=30)

            if response.status_code == 200:
                print(f"[+] Request successful")
                return response
            elif response.status_code == 403:
                print(f"[!] Access forbidden (403) - {url}")
                if USE_PROXIES:
                    proxy_rotator.mark_proxy_failed(current_proxy)
            elif response.status_code == 429:
                print(f"[!] Rate limited (429) - {url}")
                if USE_PROXIES:
                    proxy_rotator.mark_proxy_failed(current_proxy)
                time.sleep(random.randint(10, 20))  # Longer wait for rate limiting
            else:
                print(f"[!] HTTP {response.status_code} - {url}")
                if USE_PROXIES:
                    proxy_rotator.mark_proxy_failed(current_proxy)

        except requests.exceptions.SSLError as e:
            print(f"[!] SSL Error: {str(e)}")
            if USE_PROXIES:
                proxy_rotator.mark_proxy_failed(current_proxy)
        except requests.exceptions.ProxyError as e:
            print(f"[!] Proxy Error: {str(e)}")
            if USE_PROXIES:
                proxy_rotator.mark_proxy_failed(current_proxy)
        except requests.exceptions.ConnectTimeout as e:
            print(f"[!] Connection Timeout: {str(e)}")
            if USE_PROXIES:
                proxy_rotator.mark_proxy_failed(current_proxy)
        except Exception as e:
            print(f"[!] Request failed: {str(e)}")
            if USE_PROXIES:
                proxy_rotator.mark_proxy_failed(current_proxy)

        # Wait before retry with exponential backoff
        wait_time = random.randint(3, 8) * (attempt + 1)
        print(f"[*] Waiting {wait_time} seconds before retry...")
        time.sleep(wait_time)

    print(f"[!] All attempts failed for: {url}")
    return None


# Create a folder to store PDFs
os.makedirs("downloaded_pdfs", exist_ok=True)


def download_pdf(pdf_url, pdf_no):
    filename = f"{pdf_no}.pdf"
    time.sleep(random.randint(2, 20))

    try:
        response = make_request_with_retry(pdf_url)
        if not response:
            return "", ""

        soup = BeautifulSoup(response.text, "html.parser")
        a_tag = soup.find("a", id="pdfDownloadLink")

        if a_tag:
            pdf_download_url = a_tag["href"]
            time.sleep(random.randint(5, 15))

            pdf_response = make_request_with_retry(pdf_download_url)
            if pdf_response and pdf_response.status_code == 200:
                with open(os.path.join("downloaded_pdfs", filename), "wb") as f:
                    f.write(pdf_response.content)
                print(f"[+] PDF downloaded: {filename}")
                return pdf_download_url, filename
            else:
                print(f"[!] Failed to download PDF: {pdf_url}")
    except Exception as e:
        print(f"[!] Error downloading PDF {pdf_url}: {str(e)}")

    return "", ""


def download_pdf_2(pdf_url, pdf_no):
    filename = f"{pdf_no}.pdf"
    pdf_download_url = pdf_url.replace("view", "download")
    print("❤️", pdf_download_url)

    try:
        response = make_request_with_retry(pdf_download_url)

        if response and response.status_code == 200:
            with open(os.path.join("downloaded_pdfs", filename), "wb") as f:
                f.write(response.content)
            print(f"[+] PDF downloaded: {filename}")
            return pdf_download_url, filename
        else:
            print(f"[!] Failed to download PDF: {pdf_url}")
    except Exception as e:
        print(f"[!] Error downloading PDF {pdf_url}: {str(e)}")

    return "", ""


def extract_current_issue_link():
    try:
        response = make_request_with_retry(INDEX_URL)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        current_li = soup.find("li", id="current")
        return current_li.a["href"] if current_li and current_li.a else None
    except Exception as e:
        print(f"[!] Error extracting current issue link: {str(e)}")
        return None


def parse_current_issue(url):
    try:
        response = make_request_with_retry(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        breadcrumb_div = soup.find("div", id="breadcrumb")
        if not breadcrumb_div:
            return None

        h3 = breadcrumb_div.find_next("h3")
        h2 = breadcrumb_div.find_next("h2")
        print(h2)

        h2_text = h2.text.strip() if h2 else None

        match = re.search(r"(Vol\s+\d+),\s*(No\s+\d+)\s*\((\d{4})\)", h2_text)
        if match:
            volume = match.group(1)
            issue = match.group(2)
            year = int(match.group(3))

        articles = []

        tables = soup.find_all("table", class_="tocArticle")
        for idx, table in enumerate(tables, 1):
            title_tag = table.find("div", class_="tocTitle").find("a")
            doi_tag = (
                table.find("div", class_="tocDOI").find("a")
                if table.find("div", class_="tocDOI")
                else None
            )
            authors_tag = table.find("div", class_="tocAuthors")
            pdf_tag = (
                table.find("div", class_="tocGalleys").find("a", class_="file")
                if table.find("div", class_="tocGalleys")
                else None
            )
            pages_tag = table.find("div", class_="tocPages")

            title = title_tag.text.strip()
            article_link = title_tag["href"]
            doi = doi_tag.text.strip() if doi_tag else ""
            authors = authors_tag.text.strip() if authors_tag else ""
            pdf_link = pdf_tag["href"] if pdf_tag else ""
            pages = pages_tag.text.strip() if pages_tag else ""

            # Download PDF if available
            pdf_download_url = ""
            filename = ""
            if pdf_link:
                full_pdf_url = (
                    pdf_link if pdf_link.startswith("http") else BASE_URL + pdf_link
                )
                pdf_download_url, filename = download_pdf(full_pdf_url, idx)

            articles.append(
                {
                    "Volume": volume,
                    "Issue": issue,
                    "Year": year,
                    "Title": title,
                    "Article Link": article_link,
                    "DOI": doi,
                    "Authors": authors,
                    "Pages": pages,
                    "PDF URL": pdf_download_url,
                    "Downloaded PDF File": filename,
                }
            )

        return articles

    except Exception as e:
        print(f"[!] Error parsing current issue: {str(e)}")
        return None


def scrape_from_downloaded_site(url):
    print("😁")
    try:
        with open(url, "r", encoding="utf-8") as f:
            res = f.read()
        soup = BeautifulSoup(res, "html.parser")

        breadcrumb_div = soup.find("div", id="breadcrumb")
        if not breadcrumb_div:
            return None

        h3 = breadcrumb_div.find_next("h3")
        h2 = breadcrumb_div.find_next("h2")
        print(h2)

        h2_text = h2.text.strip() if h2 else None

        match = re.search(r"(Vol\s+\d+),\s*(No\s+\d+)\s*\((\d{4})\)", h2_text)
        if match:
            volume = match.group(1)
            issue = match.group(2)
            year = int(match.group(3))

        articles = []

        tables = soup.find_all("table", class_="tocArticle")
        for idx, table in enumerate(tables, 1):
            title_tag = table.find("div", class_="tocTitle").find("a")
            doi_tag = (
                table.find("div", class_="tocDOI").find("a")
                if table.find("div", class_="tocDOI")
                else None
            )
            authors_tag = table.find("div", class_="tocAuthors")
            pdf_tag = (
                table.find("div", class_="tocGalleys").find("a", class_="file")
                if table.find("div", class_="tocGalleys")
                else None
            )
            pages_tag = table.find("div", class_="tocPages")

            title = title_tag.text.strip()
            article_link = title_tag["href"]
            doi = doi_tag.text.strip() if doi_tag else ""
            authors = authors_tag.text.strip() if authors_tag else ""
            pdf_link = pdf_tag["href"] if pdf_tag else ""
            pages = pages_tag.text.strip() if pages_tag else ""

            print(title)
            print(article_link)

            pdf_download_url = ""
            filename = ""
            try:
                # Download PDF if available
                if pdf_link:
                    full_pdf_url = (
                        pdf_link if pdf_link.startswith("http") else BASE_URL + pdf_link
                    )
                    pdf_download_url, filename = download_pdf_2(full_pdf_url, idx)
            except Exception as e:
                print(f"Cannot download PDF for {title}: {str(e)}")

            articles.append(
                {
                    "Volume": volume,
                    "Issue": issue,
                    "Year": year,
                    "Title": title,
                    "Article Link": article_link,
                    "DOI": doi,
                    "Authors": authors,
                    "Pages": pages,
                    "PDF URL": pdf_download_url,
                    "Downloaded PDF File": filename,
                }
            )

        return articles

    except Exception as e:
        print(f"[!] Error scraping from downloaded site: {str(e)}")
        return None


def load_proxies_from_file(filename):
    """Load proxies from a text file (one proxy per line)"""
    try:
        with open(filename, "r") as f:
            proxies = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
        print(f"[+] Loaded {len(proxies)} proxies from {filename}")
        return proxies
    except FileNotFoundError:
        print(f"[!] Proxy file {filename} not found")
        return []


def test_proxy(proxy_url, test_url="http://httpbin.org/ip", timeout=10):
    """Test if a proxy is working"""
    try:
        # Create a simple requests session for testing
        session = requests.Session()
        session.verify = False  # Disable SSL verification for testing

        # Set proxy
        proxy_dict = {"http": proxy_url, "https": proxy_url}
        session.proxies.update(proxy_dict)

        # Add headers to look more like a real browser
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

        response = session.get(test_url, timeout=timeout)
        if response.status_code == 200:
            print(f"[+] Proxy working: {proxy_url}")
            return True
    except Exception as e:
        print(f"[!] Proxy failed: {proxy_url} - {str(e)}")
    return False


def filter_working_proxies(proxy_list, max_workers=10):
    """Filter out non-working proxies"""
    print(f"[*] Testing {len(proxy_list)} proxies...")
    working_proxies = []

    for proxy in proxy_list:
        if test_proxy(proxy):
            working_proxies.append(proxy)
        # Small delay between tests
        time.sleep(0.5)

    print(f"[+] Found {len(working_proxies)} working proxies")
    return working_proxies


def extract_h3_h2_after_breadcrumb(soup):
    breadcrumb_div = soup.find("div", id="breadcrumb")
    if not breadcrumb_div:
        return None, None

    h3 = breadcrumb_div.find_next("h3")
    h2 = breadcrumb_div.find_next("h2")

    h3_text = h3.text.strip() if h3 else None
    h2_text = h2.text.strip() if h2 else None

    return h3_text, h2_text


# Main execution
def main():
    global proxy_rotator, USE_PROXIES

    print("[*] Starting enhanced scraper with proxy rotation and SSL handling")

    # Load proxies from file if available
    if os.path.exists("proxies.txt"):
        loaded_proxies = load_proxies_from_file("proxies.txt")
        if loaded_proxies:
            PROXY_LIST.extend(loaded_proxies)

    # Convert HTTPS proxies to HTTP for better compatibility
    if USE_PROXIES and PROXY_LIST:
        converted_proxies = []
        for proxy in PROXY_LIST:
            # Convert https:// proxies to http:// to avoid SSL issues
            if proxy.startswith("https://"):
                http_proxy = proxy.replace("https://", "http://")
                converted_proxies.append(http_proxy)
                print(f"[*] Converted {proxy} to {http_proxy}")
            else:
                converted_proxies.append(proxy)

        # Test and filter working proxies
        print(f"[*] Testing {len(converted_proxies)} proxies...")
        working_proxies = filter_working_proxies(converted_proxies)
        proxy_rotator = ProxyRotator(working_proxies)

        if not working_proxies:
            print("[!] No working proxies found, disabling proxy rotation")
            USE_PROXIES = False
        else:
            print(f"[+] Using {len(working_proxies)} working proxies")

    # For live scraping (uncomment the line below)
    # current_issue_url = extract_current_issue_link()

    # For testing with downloaded file
    current_issue_url = "site.html"

    if current_issue_url:
        print("[*] Current issue URL found:", current_issue_url)

        # Choose between live scraping or local file
        if current_issue_url.startswith("http"):
            article_data = parse_current_issue(current_issue_url)
        else:
            article_data = scrape_from_downloaded_site(current_issue_url)

        if article_data:
            # Save to Excel
            df = pd.DataFrame(article_data)
            df.to_excel("samarah_current_issue.xlsx", index=False)
            print("[✓] Data saved to 'samarah_current_issue.xlsx'")
        else:
            print("[!] No article data found.")
    else:
        print("[!] Could not find current issue URL.")


if __name__ == "__main__":
    main()
