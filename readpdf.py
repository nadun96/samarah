import PyPDF2
import re


def extract_data_from_pdf(pdf_path):
    extracted_text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
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


if __name__ == "__main__":
    # Example usage
    pdf_file = "10.52756_ijerr.2025.v47.001.pdf"
    found_parts = extract_data_from_pdf(pdf_file)

    if found_parts:
        first_part = found_parts[0]
        print(f"The first extracted part is: {first_part}")
