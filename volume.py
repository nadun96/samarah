from lxml import html
import re


def extract_volume_and_year(html_content: str) -> tuple[str, str]:
    if not html_content:
        print("No HTML content provided to extract volume and year.")
        return "N/A", "N/A"

    try:
        # Parse the HTML with lxml to enable XPath queries
        tree = html.fromstring(html_content)

        # Target the h1 element specifically within the given XPath
        # The XPath provided in the request was for a div, so we append /h1.
        h1_elements = tree.xpath("/html/body/div/div[1]/div[1]/div/h1")

        if h1_elements:
            h1_text = h1_elements[0].text_content().strip()
            print(f"Found h1 text: '{h1_text}'")

            # Use regex to find "Vol. X" and a 4-digit year
            volume_match = re.search(r"Vol\.\s*(\d+)", h1_text, re.IGNORECASE)
            # Assumes year is typically in parentheses, e.g., (2024)
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


# Example Usage (replace with your actual HTML content)
if __name__ == "__main__":
    # This is a dummy HTML string representing the structure you described
    dummy_html_content = """
    <html>
    <body>
        <div>
            <div>
                <div>
                    <h1>International Journal of Engineering Research and Reviews Vol. 10, No. 3 (2024)</h1>
                    <p>Some other content</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    volume, year = extract_volume_and_year(dummy_html_content)
    print(f"Extracted Volume: {volume}, Year: {year}")

    # Example with different text format (might need regex adjustment for real cases)
    dummy_html_content_2 = """
    <html>
    <body>
        <div>
            <div>
                <div>
                    <h1>IJERR - Volume 11, Issue 1, 2025</h1>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    volume2, year2 = extract_volume_and_year(dummy_html_content_2)
    print(f"Extracted Volume: {volume2}, Year: {year2}")

    # Example where element is not found
    dummy_html_content_no_h1 = """
    <html>
    <body>
        <div>
            <div>
                <div>
                    <p>No H1 here</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    volume3, year3 = extract_volume_and_year(dummy_html_content_no_h1)
    print(f"Extracted Volume: {volume3}, Year: {year3}")
