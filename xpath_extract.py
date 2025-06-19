from lxml import html, etree
import sys


def get_xpath_expression(mode, value):
    if mode == "class":
        return f"//*[contains(concat(' ', normalize-space(@class), ' '), ' {value} ')]"
    elif mode == "id":
        return f"//*[@id='{value}']"
    elif mode == "text":
        return f"//*[contains(normalize-space(text()), '{value}')]"
    else:
        raise ValueError("Invalid mode. Use 'class', 'id', or 'text'.")


def get_xpaths(file_path, mode, value):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        tree = html.fromstring(content)
        element_tree = etree.ElementTree(tree)  # ✅ Corrected import and use

        xpath_expr = get_xpath_expression(mode, value)
        elements = tree.xpath(xpath_expr)

        print(f"Found {len(elements)} element(s) using {mode}='{value}':\n")
        for i, elem in enumerate(elements, start=1):
            path = element_tree.getpath(elem)
            print(f"{i}. {path}")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Entry point
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python xpath_extract.py <html_file_path> <mode: class|id|text> <value>"
        )
    else:
        html_file = sys.argv[1]
        mode = sys.argv[2].lower()
        value = sys.argv[3]
        get_xpaths(html_file, mode, value)
