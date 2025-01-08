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

1. **Request API Keys and Channel ID**:  
   Before running the script, ask @denilson in the Slack channel for the following:
   - **Slack API Bot Token**
   - **Slack App Token**
   - **Channel ID** for the `ohlq_email_validator` Slack channel

2. **Prepare the Slack Channel**:  
   In the `ohlq_email_validator` Slack channel, you need to submit the following:
   - **utm_campaign text** (e.g., marketing campaign or project identifier)
   - **HTML file** of the email you wish to validate

3. **Run the script**:  
   Once you have the API keys and channel ID, and you've submitted the necessary information in Slack, run the script using:

   ```bash
   python3 slack_email_qa.py

## Results

1. **Results Message**: 
   - The bot will repsond in the same thread as the original message with the html file and utm_campaign aram
   - The bot will generate two files, `full_output.txt` and `error_output.txt`.
   - The **Full Report** will contain a detailed view of the HTML structure (line numbers, attributes).
   - The **Error Report** will outline any validation issues with the HTML, with details like missing attributes or tags and broken links, along with line numbers and a breakdown of what went wrong.

