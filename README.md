# ohlq-email-qa

# HTML Link & Image Validator

This Python script validates anchor (`<a>`) and image (`<img>`) tags in HTML email files to ensure proper formatting and compliance with expected values.

## Features
- **Checks UTM parameters** (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`) in anchor tag URLs.
- **Validates image `src`** attribute starts with `https://braze-images.com`.
- **Verifies image `border`** attribute is set to `0`.
- **Checks fragment identifiers** in anchor tags.

## Requirements
- Python 3
- `slack-bolt` library (install with `pip3 install slack-bolt`)
- `slack-sdk` library (install with `pip3 install slack-sdk`)
- `requests` library (install with `pip3 install requests`)
- `beautifulsoup4` library (install with `pip3 install beautifulsoup4`)
- `python-dotenv` library (install with `pip3 install python-dotenv`)

## Installation

To install the required dependencies, you can use the following command:

```bash
pip3 install -r requirements.txt

## Usage
1. Place your HTML file in the same directory or provide its path.
2. Run the script:
   ```bash
   python validate_html.py

Check the output.txt file for the validation report.
