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
        Initialize the scraper with enhanced CloudScraper configuration
        """
        self.base_url = base_url
        self.max_articles = max_articles
        self.delay = delay
        
        # Try multiple CloudScraper configurations
        self.scraper_configs = [
            # Configuration 1: Chrome on Windows
            {
                'browser': {
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebPool/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"'
                }
            },
            # Configuration 2: Firefox on Windows  
            {
                'browser': {
                    'browser': 'firefox',
                    'platform': 'windows',
                    'desktop': True
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            },
            # Configuration 3: Chrome on Linux
            {
                'browser': {
                    'browser': 'chrome',
                    'platform': 'linux',
                    'desktop': True
                },
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            }
        ]
        
        self.current_config_index = 0
        self.scraper = None
        self.session = None
        self.articles_data = []
        
        # Initialize with first configuration
        self.initialize_scraper()

    def initialize_scraper(self, config_index=None):
        """
        Initialize or reinitialize the scraper with a specific configuration
        """
        if config_index is not None:
            self.current_config_index = config_index
        
        config = self.scraper_configs[self.current_config_index]
        
        try:
            print(f"🔧 Initializing scraper with config {self.current_config_index + 1}/{len(self.scraper_configs)}")
            
            # Create scraper with browser configuration
            self.scraper = cloudscraper.create_scraper(
                browser=config['browser'],
                delay=self.delay
            )
            
            # Update headers
            self.scraper.headers.update(config['headers'])
            
            # Add some additional headers for better compatibility
            self.scraper.headers.update({
                'DNT': '1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            })
            
            self.session = self.scraper
            print(f"✅ Scraper initialized with {config['browser']['browser']} on {config['browser']['platform']}")
            
        except Exception as e:
            print(f"❌ Error initializing scraper: {e}")
            raise

    def try_next_scraper_config(self):
        """
        Switch to the next scraper configuration
        """
        self.current_config_index = (self.current_config_index + 1) % len(self.scraper_configs)
        self.initialize_scraper()
        return self.current_config_index

    def handle_403_forbidden(self, url):
        """
        Handle 403 Forbidden errors with multiple strategies
        """
        print("🚫 403 Forbidden Error - Trying advanced bypass methods...")
        
        strategies = [
            self.strategy_change_scraper_config,
            self.strategy_add_referer,
            self.strategy_session_warmup,
            self.strategy_manual_browser_session
        ]
        
        for i, strategy in enumerate(strategies, 1):
            print(f"🔄 Trying strategy {i}/{len(strategies)}: {strategy.__name__}")
            
            try:
                response = strategy(url)
                if response and response.status_code == 200:
                    print(f"✅ Strategy {i} successful!")
                    return response
                else:
                    print(f"❌ Strategy {i} failed")
                    
            except Exception as e:
                print(f"❌ Strategy {i} error: {e}")
                
            # Wait between strategies
            time.sleep(5)
        
        print("💥 All strategies failed")
        return None

    def strategy_change_scraper_config(self, url):
        """
        Strategy 1: Try different browser configurations
        """
        original_config = self.current_config_index
        
        # Try all configurations
        for _ in range(len(self.scraper_configs)):
            self.try_next_scraper_config()
            if self.current_config_index == original_config:
                break  # We've tried all configurations
                
            try:
                time.sleep(3)
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response
            except:
                continue
                
        return None

    def strategy_add_referer(self, url):
        """
        Strategy 2: Add referer and additional headers
        """
        # Add referer header
        base_domain = '/'.join(url.split('/')[:3])
        self.session.headers.update({
            'Referer': base_domain,
            'Origin': base_domain,
            'X-Requested-With': 'XMLHttpRequest',
        })
        
        try:
            response = self.session.get(url, timeout=30)
            return response
        except:
            return None

    def strategy_session_warmup(self, url):
        """
        Strategy 3: Warm up the session by visiting the homepage first
        """
        try:
            base_domain = '/'.join(url.split('/')[:3])
            homepage_url = f"{base_domain}/index.php/samarah"
            
            print(f"🏠 Warming up session with homepage: {homepage_url}")
            
            # Visit homepage first
            homepage_response = self.session.get(homepage_url, timeout=30)
            time.sleep(2)
            
            # Then visit the target URL
            response = self.session.get(url, timeout=30)
            return response
            
        except Exception as e:
            print(f"Session warmup error: {e}")
            return None

    def strategy_manual_browser_session(self, url):
        """
        Strategy 4: Guide user to get cookies from browser
        """
        print("\n" + "="*60)
        print("🌐 MANUAL BROWSER SESSION REQUIRED")
        print("="*60)
        print("The website is blocking automated requests.")
        print("Let's get cookies from your browser session:")
        print()
        print("📋 STEP-BY-STEP INSTRUCTIONS:")
        print("1. Open your web browser")
        print(f"2. Go to: {url}")
        print("3. Complete any verification (checkbox, captcha, etc.)")
        print("4. Once you can see the page content, press F12")
        print("5. Go to Console tab and paste this code:")
        print()
        print("   document.cookie")
        print()
        print("6. Copy the output and paste it below")
        print("7. Press Enter")
        print("-"*60)
        
        cookie_string = input("🍪 Paste browser cookies here: ").strip()
        
        if cookie_string:
            # Parse cookies
            try:
                # Clear existing cookies
                self.session.cookies.clear()
                
                # Add new cookies
                cookie_pairs = cookie_string.split(';')
                for pair in cookie_pairs:
                    if '=' in pair:
                        name, value = pair.split('=', 1)
                        self.session.cookies.set(name.strip(), value.strip())
                        
                print(f"✅ Added {len(cookie_pairs)} cookies to session")
                
                # Try accessing the page
                response = self.session.get(url, timeout=30)
                return response
                
            except Exception as e:
                print(f"❌ Error processing cookies: {e}")
                
        return None
        """
        Handle checkbox verification challenges specifically
        """
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for checkbox verification forms
        checkboxes = soup.find_all('input', {'type': 'checkbox'})
        verification_forms = soup.find_all('form')
        
        # Check for checkbox verification indicators
        checkbox_indicators = [
            'i am not a robot', 'verify you are human', 'check the box',
            'tick the checkbox', 'human verification', 'security check'
        ]
        
        page_text = soup.get_text().lower()
        has_checkbox_verification = any(indicator in page_text for indicator in checkbox_indicators)
        
        if has_checkbox_verification or checkboxes:
            print(f"☑️  Checkbox verification detected on {url}")
            print("📋 Checkbox verification detected!")
            
            # Try to find and analyze the verification form
            for form in verification_forms:
                form_text = form.get_text().lower()
                if any(indicator in form_text for indicator in checkbox_indicators):
                    print(f"🔍 Found verification form: {form.get('action', 'No action')}")
                    
                    # Look for hidden fields or tokens
                    hidden_inputs = form.find_all('input', {'type': 'hidden'})
                    if hidden_inputs:
                        print(f"🔐 Found {len(hidden_inputs)} hidden form fields")
                    
                    # Try to extract form data
                    form_data = {}
                    for input_field in form.find_all('input'):
                        name = input_field.get('name')
                        value = input_field.get('value', '')
                        input_type = input_field.get('type', 'text')
                        
                        if name:
                            if input_type == 'checkbox':
                                # Set checkbox as checked
                                form_data[name] = 'on' if not value else value
                                print(f"☑️  Checkbox field: {name} = on")
                            elif input_type == 'hidden':
                                form_data[name] = value
                                print(f"🔐 Hidden field: {name} = {value[:20]}...")
                            else:
                                form_data[name] = value
                    
                    # Try to submit the form automatically
                    form_action = form.get('action')
                    form_method = form.get('method', 'post').lower()
                    
                    if form_action:
                        submit_url = urljoin(url, form_action)
                        print(f"🚀 Attempting to submit form to: {submit_url}")
                        
                        try:
                            if form_method == 'post':
                                submit_response = self.session.post(submit_url, data=form_data)
                            else:
                                submit_response = self.session.get(submit_url, params=form_data)
                            
                            if not self.is_verification_page(submit_response):
                                print("✅ Checkbox verification passed automatically!")
                                return submit_response
                            else:
                                print("⚠️  Automatic submission failed, trying manual approach...")
                        except Exception as e:
                            print(f"❌ Form submission error: {e}")
            
            # Fallback to manual intervention
            return self.manual_verification_handler(url)
        
        return response

    def manual_verification_handler(self, url):
        """
        Handle manual verification with guided instructions
        """
        print("\n" + "="*60)
        print("🚨 MANUAL VERIFICATION REQUIRED")
        print("="*60)
        print(f"🌐 URL: {url}")
        print("\n📋 INSTRUCTIONS:")
        print("1. Open the URL above in your browser")
        print("2. Complete the checkbox verification (tick the box)")
        print("3. Wait for the page to load completely")
        print("4. Copy any cookies if prompted")
        print("5. Come back here and press Enter")
        print("\n⏳ The script will wait for you...")
        print("-"*60)
        
        input("✅ Press Enter after completing the checkbox verification...")
        
        # After manual verification, try to continue with the session
        print("🔄 Attempting to continue with updated session...")
        
        # Try to access the page again
        try:
            response = self.session.get(url)
            if not self.is_verification_page(response):
                print("✅ Manual verification successful!")
                return response
            else:
                print("⚠️  Still showing verification page...")
                
                # Offer cookie/session transfer option
                print("\n🍪 If verification persists, you can:")
                print("1. Copy browser cookies to this session")
                print("2. Try a different approach")
                
                choice = input("Enter 'cookies' to transfer cookies, or 'continue' to proceed anyway: ").lower()
                
                if choice == 'cookies':
                    return self.handle_cookie_transfer(url)
                else:
                    return response
                    
        except Exception as e:
            print(f"❌ Error after manual verification: {e}")
            return None

    def handle_cookie_transfer(self, url):
        """
        Guide user through cookie transfer process
        """
        print("\n🍪 COOKIE TRANSFER GUIDE:")
        print("-"*40)
        print("1. In your browser, press F12 (Developer Tools)")
        print("2. Go to Application/Storage tab")
        print("3. Click on 'Cookies' in the left panel")
        print("4. Find the domain cookies and copy them")
        print("5. Paste them below (format: name=value)")
        print("\nExample: session_id=abc123; csrf_token=xyz789")
        print("\nEnter cookies (or press Enter to skip):")
        
        cookie_input = input().strip()
        
        if cookie_input:
            # Parse and add cookies to session
            try:
                cookie_pairs = cookie_input.split(';')
                for pair in cookie_pairs:
                    if '=' in pair:
                        name, value = pair.split('=', 1)
                        self.session.cookies.set(name.strip(), value.strip())
                        print(f"🍪 Added cookie: {name.strip()}")
                
                print("✅ Cookies added to session")
                
                # Try accessing the page again
                response = self.session.get(url)
                return response
                
            except Exception as e:
                print(f"❌ Error processing cookies: {e}")
        
        print("⏭️  Continuing without cookies...")
        return self.session.get(url)

    def handle_verification_challenge(self, response, url):
        """
        Enhanced verification handler with checkbox support
        """
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check for common verification indicators
        verification_indicators = [
            'captcha', 'verification', 'challenge', 'human', 
            'robot', 'security check', 'please verify', 'checkbox',
            'tick', 'check the box', 'i am not a robot'
        ]
        
        page_text = soup.get_text().lower()
        
        if any(indicator in page_text for indicator in verification_indicators):
            print(f"⚠️  Human verification detected on {url}")
            
            # First try checkbox-specific handling
            checkbox_response = self.handle_checkbox_verification(response, url)
            if checkbox_response != response:
                return checkbox_response
            
            # Strategy 1: Wait and retry with longer delays
            print("🔄 Trying automatic resolution...")
            for attempt in range(2):
                print(f"⏳ Waiting attempt {attempt + 1}/2...")
                time.sleep(15 + (attempt * 10))  # Progressive delay
                
                retry_response = self.session.get(url)
                if not self.is_verification_page(retry_response):
                    print("✅ Verification passed automatically!")
                    return retry_response
            
            # Strategy 2: Manual intervention
            return self.manual_verification_handler(url)
        
        return response

    def is_verification_page(self, response):
        """
        Check if the response contains verification challenges
        """
        if not response:
            return True
            
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        verification_keywords = [
            'verify you are human', 'captcha', 'cloudflare', 
            'security check', 'please wait', 'checking your browser',
            'challenge', 'robot', 'automated', 'checkbox',
            'i am not a robot', 'tick the box', 'check the box'
        ]
        
        return any(keyword in page_text for keyword in verification_keywords)

    def get_page_with_verification_handling(self, url, max_retries=3):
        """
        Enhanced page fetching with 403 handling and verification
        """
        for attempt in range(max_retries):
            try:
                print(f"🌐 Fetching: {url} (Attempt {attempt + 1}/{max_retries})")
                
                # Add random delay to appear more human-like
                human_delay = self.delay + (attempt * 2)
                time.sleep(human_delay)
                
                response = self.session.get(url, timeout=30)
                
                # Handle different response codes
                if response.status_code == 403:
                    print(f"🚫 403 Forbidden detected (Attempt {attempt + 1})")
                    
                    # Try 403 handling strategies
                    bypass_response = self.handle_403_forbidden(url)
                    if bypass_response:
                        response = bypass_response
                    else:
                        if attempt < max_retries - 1:
                            print(f"⏳ Waiting before retry...")
                            time.sleep(30)
                            continue
                        else:
                            print("❌ Could not bypass 403 after all attempts")
                            return None
                
                elif response.status_code == 200:
                    # Check if we hit a verification page
                    if self.is_verification_page(response):
                        print(f"🔒 Verification challenge detected (Attempt {attempt + 1})")
                        response = self.handle_verification_challenge(response, url)
                        
                        # Verify the challenge was resolved
                        if self.is_verification_page(response):
                            if attempt < max_retries - 1:
                                print(f"⏳ Verification not resolved, waiting before retry...")
                                time.sleep(30)
                                continue
                            else:
                                print("❌ Could not bypass verification after all attempts")
                                return None
                else:
                    response.raise_for_status()
                
                print("✅ Page fetched successfully")
                return response
                
            except requests.exceptions.Timeout:
                print(f"⏰ Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(15)
                    continue
                    
            except requests.RequestException as e:
                print(f"❌ Request error on attempt {attempt + 1}: {e}")
                
                # If it's a 403, try handling it
                if "403" in str(e):
                    bypass_response = self.handle_403_forbidden(url)
                    if bypass_response:
                        return bypass_response
                
                if attempt < max_retries - 1:
                    time.sleep(10)
                    continue
                    
        print(f"💥 Failed to fetch {url} after {max_retries} attempts")
        return None

    def handle_checkbox_verification(self, response, url):
        pass

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
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'articles_processed': len(self.articles_data),
            'articles_data': self.articles_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Progress saved to {filename}")

    def load_progress(self, filename="scraping_progress.json"):
        """
        Load previous progress to resume scraping
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                self.articles_data = progress_data.get('articles_data', [])
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

        filename = f"{year or 'unknown'}_Vol{volume or 'x'}_No{issue or 'x'}_{safe_title}.pdf"
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
        for i, article_table in enumerate(article_tables[start_index:], start_index + 1):
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
                "scraped_at": datetime.now().isoformat()
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
            df.to_csv(filename, index=False, encoding='utf-8')
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
            1 for article in scraper.articles_data 
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