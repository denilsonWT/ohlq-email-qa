import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Slack API tokens from environment variables
slack_api_token = os.getenv("SLACK_API_TOKEN")
slack_app_token = os.getenv("SLACK_APP_TOKEN")
signature_verifier = SignatureVerifier(slack_app_token)

# Initialize Slack WebClient
web_client = WebClient(token=slack_api_token)

# Flask App setup
app = Flask(__name__)

# Constants for Slack Channel and error messages
EMAIL_QA_AUTOMATION_CHANNEL_ID = "C0883CP5U3E"
ERROR_NEW_REQUEST_PROMPT = "\nPlease start a new thread!"
ERROR_INVALID_UTM_MISSING = "Error: missing utm parameter! please start new message thread with a utm campaign parameter"
ERROR_INVALID_UTM_FORMAT = "Error: space in utm paramter! please start new message thread with a proper utm campaign parameter"
ERROR_FILE_NOT_FOUND = "Error: missing html file! please start new message thread with an html file"
ERROR_FILE_MULTIPLE = "Error: multiple html files uploaded! please start new message thread with 1 file"
ERROR_FILE_NOT_HTML = "Error: incorrect file type submitted! please start new message thread with html file"
ERROR_FILE_HTTP_REQUEST = "Error: https file request failed code: "
FILE_PATH_REPORT_ERRORS = "error_output.txt"
FILE_PATH_REPORT_FULL = "full_output.txt"
MESSAGE_TEXT_FULL_REPORT = ""
MESSAGE_TEXT_ERROR_REPORT = ""


def check_image_attributes(image_tag):
    full_report = []
    error_report = []
    src_line = image_tag.sourceline
    full_report.append(f"🏞️  Image\n")
    full_report.append(f"Line number: {src_line}\n")
    
    src = image_tag.get('src', '')

    if src.startswith("https://braze-images.com"):
        full_report.append(f"💚 Link src formatted properly\n")
    else:
        full_report.append(f"❌ Incorrect link src: {src} \nmissing correct pre-fix braze-images.com/\n")
        error_report.append(f"❌ Incorrect link src: {src} \nmissing correct pre-fix braze-images.com/\n")

    border_value = image_tag.get('border')
    if border_value != '0':
        full_report.append(f"❌ Incorrect border value: {border_value}\n")
        error_report.append(f"❌ Incorrect border value: {border_value}\n")
    else:
        full_report.append(f"💚 Correct border value: 0\n")
    
    if error_report:
        error_report.insert(0, f"Line number: {src_line}\n")
        error_report.insert(0, f"🏞️  Image\n")
        error_report.append('\n')
    
    full_report.append('\n')
    return full_report, error_report

def check_query_params(tag, utm_campaign):
    href = tag['href']

    expected_utm_param_values = {
        'utm_source': 'braze',
        'utm_medium': 'email',
        'utm_campaign': utm_campaign,
        'utm_content': '',
        'utm_term': '',
    }
    
    full_report = []
    error_report = []

    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    
    full_report.append(f"🔗 Link {href}\n")
    full_report.append(f"Line number: {tag.sourceline}\n")

    for key, value in expected_utm_param_values.items():
        if key not in query_params:
            full_report.append(f"❌ Missing utm parameter: {key}\n")
            error_report.append(f"❌ Missing utm parameter: {key}\n")   
        else:
            param_given_value = query_params[key][0]
        
            if key in ['utm_content', 'utm_term']:
                if not param_given_value:
                    full_report.append(f"❌ Empty utm parameter: {key}\n")
                    error_report.append(f"❌ Empty utm parameter: {key}\n")   
                else:
                    full_report.append(f"💡 {key}: {param_given_value}\n")
            elif param_given_value != value:
                full_report.append(f"❌ {key} value is incorrect. Expected '{value}', but got '{param_given_value}'\n")
                error_report.append(f"❌ {key} value is incorrect. Expected '{value}', but got '{param_given_value}'\n")  
            elif param_given_value == value:
                full_report.append(f"💚 {key}: {param_given_value}\n")

    if error_report:
        error_report.insert(0, f"Line number: {tag.sourceline}\n")
        error_report.insert(0, f"🔗 Link {href}\n")
        error_report.append('\n')
    
    full_report.append('\n')
    return full_report, error_report

def check_frag_id(tag, anchor_tags_with_name):
    error_report = []
    full_report = []
    href = tag['href']

    if href[1:] in anchor_tags_with_name:
        full_report.append(f"🔎 Fragment Identifier:\nLine number: {tag.sourceline}\n💚 {href[1:]} ref found in file\n\n")
    else:
        error_report.append(f"🔎 Fragment Identifier:\nLine number: {tag.sourceline}\n❌ {href[1:]} ref not found in file\n\n")
    
    return full_report, error_report

def check_html_file(file, utm_campaign):
    soup = BeautifulSoup(file, 'html.parser')
    anchor_img_tags = soup.find_all(['a', 'img'])
    anchor_tags_with_name = [tag.attrs['name'] for tag in anchor_img_tags if 'name' in tag.attrs]
    
    full_report_parts = []
    error_report_parts = []
    
    for tag in anchor_img_tags:
        if tag.name == 'a':
            if 'href' in tag.attrs.keys():
                href = tag['href']
                if href.startswith('#'):
                    full_report_tag, error_report_tag = check_frag_id(tag, anchor_tags_with_name)

                    full_report_parts.extend(full_report_tag)
                    if error_report_tag:
                        error_report_parts.extend(error_report_tag)
                else:
                    full_report_params, error_report_params = check_query_params(tag=tag, utm_campaign=utm_campaign)
                    full_report_parts.extend(full_report_params)
                    if error_report_params:
                        error_report_parts.extend(error_report_params)
        else:
            full_report_img, error_report_img = check_image_attributes(image_tag=tag)
            full_report_parts.extend(full_report_img)
            if error_report_img:
                error_report_parts.extend(error_report_img)
        
    return ''.join(full_report_parts), ''.join(error_report_parts)

def verify_input(utm_campaign, files):
    if not utm_campaign:
        return True, ERROR_INVALID_UTM_MISSING
    elif " " in utm_campaign:
        return True, ERROR_INVALID_UTM_FORMAT
    elif not files:
        return True, ERROR_FILE_NOT_FOUND
    elif len(files) > 1:
        return True, ERROR_FILE_MULTIPLE
    elif not files[0]['filetype'] == 'html':
        return True, ERROR_FILE_NOT_HTML
    else:
        return False, None

def send_error_message(channel, thread_ts, error_message):
    try:
        web_client.chat_postMessage(
            channel=channel,
            text=error_message,
            thread_ts=thread_ts
        )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def create_final_response(web_client: WebClient, report, file_path,thread_ts,channel, message_txt):
    with open(file_path, 'w') as file:
        file.write(report)

    file_size = os.path.getsize(file_path)

    file_url_response = web_client.files_getUploadURLExternal(
    filename=file_path,
    length=file_size
    )

    if file_url_response['ok'] == True:
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_path, file),
            }
                
        # Send a POST request to the upload URL with the file content
            http_upload_response = requests.post(file_url_response['upload_url'], files=files)

            if http_upload_response.status_code==200:
                try:
                    web_client.files_completeUploadExternal(
                        files=[{"id":file_url_response['file_id'],"title":file_path}],
                        channel_id=channel,
                        initial_comment=message_txt,
                        thread_ts=thread_ts
                    )
                except SlackApiError as e:
                    print(f"Error sending message: {e.response['error']}")
            else:
                print('Error with file API')

# Flask route to handle Slack events
@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return "Request verification failed", 400

    data = request.json
    if "event" in data:
        event = data["event"]
        channel = event["channel"]

        # if event["type"] == "message" and "bot_id" not in event and channel == EMAIL_QA_AUTOMATION_CHANNEL_ID:
        if event["type"] == "message" and "bot_id" not in event:

            thread_ts = event.get('thread_ts', event['ts']) 
            if thread_ts == event['ts']:
                utm_campaign = event.get('text', '').strip()  
                files = event.get('files', [])

                error_flag, error_message = verify_input(utm_campaign, files)

                if error_flag:
                    send_error_message(channel, thread_ts, error_message)
                else:
                    file_url = files[0]['url_private']
                    headers = {"Authorization": f"Bearer {slack_api_token}"}
                    file_response = requests.get(file_url, headers=headers)
                    
                    if file_response.status_code == 200:
                        html_content = file_response.text

                        full_report, error_report = check_html_file(html_content, utm_campaign)

                        create_final_response(
                            web_client=web_client,
                            report=full_report,
                            file_path=FILE_PATH_REPORT_FULL,
                            thread_ts=thread_ts,
                            channel=channel,
                            message_txt=MESSAGE_TEXT_FULL_REPORT
                        )

                        create_final_response(
                            web_client=web_client,
                            report=error_report,
                            file_path=FILE_PATH_REPORT_ERRORS,
                            thread_ts=thread_ts,
                            channel=channel,
                            message_txt=MESSAGE_TEXT_ERROR_REPORT
                        )
                    
                    else:
                        send_error_message(web_client, channel, thread_ts, ERROR_FILE_HTTP_REQUEST + file_response.text + ERROR_NEW_REQUEST_PROMPT)
        else:
            send_error_message(web_client, channel, thread_ts, ERROR_NEW_REQUEST_PROMPT)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
