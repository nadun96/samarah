## Libraries Used (As Requested):
- ✅ `os` - File/directory operations
- ✅ `csv` - CSV file handling (alternative method provided)  
- ✅ `time` - Delays between requests
- ✅ `requests` (via `cloudscraper`) - HTTP requests with session support
- ✅ `cloudscraper` - Main scraping engine
- ✅ `datetime` - Timestamps for logging
- ✅ `BeautifulSoup` - HTML parsing
- ✅ `urljoin, quote` - URL utilities (imported but ready to use)
- ✅ `json` - JSON file export
- ✅ `pandas` - DataFrame and CSV export
- ✅ `re` - Regular expressions for text parsing

## Key Changes Made:

### 1. **Custom Logger Class**
```python
class Logger:
    """Simple logger using only standard libraries"""
```
- Replaces complex logging library
- Writes to both console and file
- Supports INFO, WARNING, ERROR levels

### 2. **Utility Functions**
```python
def sanitize_filename(text, max_length=50)
def random_delay(min_seconds=2, max_seconds=5)  
```
- Standalone functions using only specified libraries
- Clean, reusable code

### 3. **Session-Based Requests**
- Uses `cloudscraper.create_scraper()` as session
- Maintains cookies and connection pooling
- More efficient than individual requests

### 4. **Dual CSV Export Methods**
```python
save_to_csv()        # Using pandas (primary)
save_to_csv_manual() # Using csv module (fallback)
```

### 5. **JSON Export Added**
```python
save_summary_json()  # Export complete data as JSON
```
- Includes timestamp, summary stats, and all article data
- Uses built-in `json` module

### 6. **Enhanced Error Handling**
- All exceptions converted to strings with `str(e)`
- Graceful degradation when operations fail
- Detailed logging of all operations

### 7. **Clean Architecture**
- No external dependencies beyond specified libraries
- All methods are self-contained
- Easy to extend or modify

## Usage Examples:

```python
# Basic usage
scraper = IJERRScraper(max_articles=10)
articles = scraper.scrape_current_issue()
csv_file = scraper.save_to_csv()

# Save as JSON instead/additionally  
json_file = scraper.save_summary_json()

# Use manual CSV if pandas not working
csv_file = scraper.save_to_csv_manual()
```

## Output Files:
- **CSV**: `IJERR_Vol{X}_{YEAR}_articles.csv`
- **JSON**: `IJERR_Vol{X}_{YEAR}_summary.json` 
- **Log**: `ijerr_scraper.log`
- **PDFs**: `pdfs/{sanitized_doi}.pdf`
