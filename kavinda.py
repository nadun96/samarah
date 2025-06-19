import requests
from bs4 import BeautifulSoup
import os
import pandas as pd
import re
import time
import random

# Step 1: Get Current Issue page
BASE_URL = "https://jurnal.ar-raniry.ac.id"
INDEX_URL = f"{BASE_URL}/index.php/samarah/index"

# Create a folder to store PDFs
os.makedirs("downloaded_pdfs", exist_ok=True)


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,si;q=0.8",
    "cache-control": "max-age=0",
    "content-length": "4995",
    "content-type": "application/x-www-form-urlencoded",
    "cookie": "HstCfa4473498=1750162142755; HstCmu4473498=1750162142755; __dtsu=51A01740039281B7194034E9DC494DA8; _cc_id=58b2be828e51571f94b5fdc6dda53b23; panoramaId=de2490231d19d03b1621f6fd145f16d53938aa3e23cf56160942c0716a9798f2; panoramaIdType=panoIndiv; OJSSID=r5hfpmsnnai42qds61u82qedr2; HstCnv4473498=4; panoramaId_expiry=1750910723945; HstCla4473498=1750306586622; HstPn4473498=9; HstPt4473498=29; HstCns4473498=8; cf_clearance=LbHNF2lbKJByyic6vETHKXS6GLZ6jKJpd9fAHYPGJSU-1750306769-1.2.1.1-5l_ogmo9.hAaV.tZm3B2dhBJev0vMRc7s6xNRIfdotQIPe94Yrmc32Rrka5fuzcJiV.oqEw6PsSBq_Je5wUyNfVKiEvL16Rfzhiq_2HwODm4YZ1AEVrF0PmkWhlTziv35ZU9G_ZunD_r1D6RvuNWb4cpGUg72iCxo4J5.gOXOiN21x2xac8gJxnljnEEvT2Qp0Sindqk0fqy1Uuo4XwqXknQ2cn1e6Qea.A1XZDQ9rd0wEA98HcSf1j4qPwdfhzPhqZ23QXOQN9ZX97P23YxbE5N44BN5t0RgR4eEIYSoaO2fP4ZuCOK_A9SytsNVCS1OYE4_320bBKx6W18emcm9ZPWRFMKRjvbYhjbkjqOzxS54gzmQcI4xx5pjyb9P",
    "origin": "https://jurnal.ar-raniry.ac.id",
    "priority": "u=0, i",
    "referer": "https://jurnal.ar-raniry.ac.id/index.php/samarah/announcement?__cf_chl_tk=SUhPLEOkBBaBX3BVY5Kfact0jIhQ9JSmfUzBbLmVcVo-1750306730-1.0.1.1-wvy4XTRvWMaDZbddWCIjvi_Z6wR6Ee6ePj_VnewE82I",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-arch": '""',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": "137.0.7151.105",
    "sec-ch-ua-full-version-list": '"Google Chrome";v="137.0.7151.105", "Chromium";v="137.0.7151.105", "Not/A)Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-model": '"Nexus 5"',
    "sec-ch-ua-platform": '"Android"',
    "sec-ch-ua-platform-version": "6.0",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
}


def download_pdf(pdf_url, pdf_no):
    filename = f"{pdf_no}.pdf"
    time.sleep(random.randint(2, 20))
    response = requests.get(pdf_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    a_tag = soup.find("a", id="pdfDownloadLink")
    if a_tag:
        pdf_download_url = a_tag["href"]
        time.sleep(random.randint(5, 15))
        response = requests.get(pdf_download_url, headers=headers)
        if response.status_code == 200:
            with open(os.path.join("downloaded_pdfs", filename), "wb") as f:
                f.write(response.content)
            print(f"[+] PDF downloaded: {filename}")
            return pdf_download_url, filename
        else:
            print(f"[!] Failed to download PDF: {pdf_url}")
    return "", ""


def download_pdf_2(pdf_url, pdf_no):
    filename = f"{pdf_no}.pdf"
    pdf_download_url = pdf_url.replace("view", "download")
    print("❤️", pdf_download_url)

    # headers = {
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    # }

    response = requests.get(pdf_download_url, headers=headers)
    print("response : ", response)
    if response:
        with open(os.path.join("downloaded_pdfs", filename), "wb") as f:
            f.write(response.content)
        print(f"[+] PDF downloaded: {filename}")
        return pdf_download_url, filename
    else:
        print(f"[!] Failed to download PDF: {pdf_url}")
    return "", ""


def extract_current_issue_link():
    res = requests.get(INDEX_URL, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    current_li = soup.find("li", id="current")
    return current_li.a["href"] if current_li and current_li.a else None


def parse_current_issue(url):
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    breadcrumb_div = soup.find("div", id="breadcrumb")
    if not breadcrumb_div:
        return None, None

    h3 = breadcrumb_div.find_next("h3")
    h2 = breadcrumb_div.find_next("h2")
    print(h2)

    # h3_text = h3.text.strip() if h3 else None
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
        if pdf_link:
            full_pdf_url = (
                pdf_link if pdf_link.startswith("http") else BASE_URL + pdf_link
            )

            # filename = title.replace(" ", "_").replace("/", "_")[:100] + ".pdf"
            # filename =  f"{idx}.pdf"
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


def scrape_from_downloaded_site(url):
    print("😁")
    # res = requests.get(url)
    with open(url, "r", encoding="utf-8") as f:
        res = f.read()
    soup = BeautifulSoup(res, "html.parser")

    breadcrumb_div = soup.find("div", id="breadcrumb")
    if not breadcrumb_div:
        return None, None

    h3 = breadcrumb_div.find_next("h3")
    h2 = breadcrumb_div.find_next("h2")
    print(h2)

    # h3_text = h3.text.strip() if h3 else None
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

        try:
            # Download PDF if available
            if pdf_link:
                full_pdf_url = (
                    pdf_link if pdf_link.startswith("http") else BASE_URL + pdf_link
                )

                # filename = title.replace(" ", "_").replace("/", "_")[:100] + ".pdf"
                # filename =  f"{idx}.pdf"
                pdf_download_url, filename = download_pdf_2(full_pdf_url, idx)
        except:
            print("can not download")

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


def extract_h3_h2_after_breadcrumb(soup):
    breadcrumb_div = soup.find("div", id="breadcrumb")
    if not breadcrumb_div:
        return None, None

    h3 = breadcrumb_div.find_next("h3")
    h2 = breadcrumb_div.find_next("h2")

    h3_text = h3.text.strip() if h3 else None
    h2_text = h2.text.strip() if h2 else None

    return h3_text, h2_text


# Execute steps
current_issue_url = extract_current_issue_link()
# current_issue_url = "https://jurnal.ar-raniry.ac.id/index.php/samarah/issue/view/1249"
# current_issue_url = "site.html"
if current_issue_url:
    print("[*] Current issue URL found:", current_issue_url)
    # article_data = parse_current_issue(current_issue_url)
    article_data = scrape_from_downloaded_site(current_issue_url)

    # Save to Excel
    df = pd.DataFrame(article_data)
    df.to_csv("samarah_current_issue.csv", index=False)
    print("[✓] Data saved to 'samarah_current_issue.csv'")
else:
    print("[!] Could not find current issue URL.")
