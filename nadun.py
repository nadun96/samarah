import cloudscraper
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import time
import random

# Step 1: Get Current Issue page
BASE_URL = "https://jurnal.ar-raniry.ac.id"
INDEX_URL = f"{BASE_URL}/index.php/samarah/index"

# Create a CloudScraper session
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "desktop": True}
)

# Create a folder to store PDFs
os.makedirs("downloaded_pdfs", exist_ok=True)


def download_pdf(pdf_url, pdf_no):
    filename = f"{pdf_no}.pdf"
    time.sleep(random.randint(2, 20))

    try:
        response = scraper.get(pdf_url)
        soup = BeautifulSoup(response.text, "html.parser")
        a_tag = soup.find("a", id="pdfDownloadLink")

        if a_tag:
            pdf_download_url = a_tag["href"]
            time.sleep(random.randint(5, 15))

            response = scraper.get(pdf_download_url)
            if response.status_code == 200:
                with open(os.path.join("downloaded_pdfs", filename), "wb") as f:
                    f.write(response.content)
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
        response = scraper.get(pdf_download_url)
        print("response:", response)

        if response.status_code == 200:
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
        res = scraper.get(INDEX_URL)
        soup = BeautifulSoup(res.text, "html.parser")
        current_li = soup.find("li", id="current")
        return current_li.a["href"] if current_li and current_li.a else None
    except Exception as e:
        print(f"[!] Error extracting current issue link: {str(e)}")
        return None


def parse_current_issue(url):
    try:
        res = scraper.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

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
    # For live scraping (uncomment the line below)
    current_issue_url = extract_current_issue_link()

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
