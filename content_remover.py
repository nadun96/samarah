import re
import os


def remove_html_content_and_whitespaces(input_filepath):
    """
    Removes all content data, keeping only HTML tags, and also removes
    unnecessary whitespace from an HTML file.

    Args:
        input_filepath (str): The path to the input HTML file.

    Returns:
        str or None: The path to the processed output file if successful,
                     otherwise None.
    """
    try:
        # Read the content of the input HTML file
        with open(input_filepath, "r", encoding="utf-8") as f:
            html_content = f.read()

        print(f"Processing '{input_filepath}' to extract tags only...")

        # 1. Remove HTML comments (multi-line aware)
        # This regex matches '<!--' followed by any characters (non-greedy)
        # until '-->'
        html_content = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)

        # 2. Remove all content between HTML tags
        # This regex uses positive lookarounds to match content that is
        # preceded by '>' and followed by '<'. It replaces this content
        # with an empty string, effectively leaving only the tags.
        # It also handles cases like <p>  Text  </p> by removing the text.
        html_content = re.sub(r"(?<=>)[^<]*(?=<)", "", html_content)

        # 3. Replace sequences of whitespace (spaces, tabs, newlines) with a single space
        # This cleans up any remaining whitespace from comments or removed content.
        html_content = re.sub(r"\s+", " ", html_content)

        # 4. Remove whitespace directly between HTML tags (e.g., `> <` becomes `><`)
        # This is a common minification step that doesn't affect rendering.
        html_content = re.sub(r">\s*<", "><", html_content)

        # 5. Strip leading/trailing whitespace from the entire string
        html_content = html_content.strip()

        # Construct the output filename
        directory, filename = os.path.split(input_filepath)
        name, ext = os.path.splitext(filename)
        # Changed output filename to reflect the new functionality
        output_filename = f"{name}_tags_only{ext}"
        output_filepath = os.path.join(directory, output_filename)

        # Write the processed content to the new file
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Content removed. Tags-only HTML saved to '{output_filepath}'")
        return output_filepath

    except FileNotFoundError:
        print(f"Error: The file '{input_filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    # Example Usage:
    # Make sure you have an 'input.html' file in the same directory
    # or provide a full path.
    input_file = r"D:\Innodata\Scraping\toc.html" # Replace with your HTML file path

    # Create a dummy input.html for testing if it doesn't exist
    if not os.path.exists(input_file):
        print(f"Creating a dummy '{input_file}' for demonstration.")
        dummy_content = """
<!DOCTYPE html>
<html>
<head>
    <title>   My Test Page   </title>
    <!-- This is a comment -->
    <style>
        body {
            font-family: sans-serif;
            margin:   20px;
        }
        h1 {
            color:  #333;
        }
    </style>
</head>
<body>
    <h1>    Hello,   World!   </h1>


    <p>
        This is a paragraph with
        multiple
        lines and      extra   spaces.
    </p>
    <div>
        Another div
        <span> and a span </span>
    </div>
</body>
</html>
        """
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(dummy_content)
        print(f"Dummy '{input_file}' created. Please run the script again.")
    else:
        remove_html_content_and_whitespaces(input_file)
