from slack_bolt import App
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from slack_sdk.errors import SlackApiError
import os
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from slack_sdk.signature import SignatureVerifier

app = Flask(__name__)


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
EMAIL_QA_AUTOMATION_CHANNEL_ID = "C0883CP5U3E"

load_dotenv()

slack_api_token = os.getenv("SLACK_API_TOKEN")
slack_app_token = os.getenv("SLACK_APP_TOKEN")
signature_verifier = SignatureVerifier(slack_app_token)

web_client = WebClient(token=slack_api_token)

client = SocketModeClient(
    app_token=slack_app_token,
    web_client=web_client
)

def check_image_attributes(image_tag):

    full_report=[]
    error_report=[]
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
    if border_value!='0':
        full_report.append(f"❌ Incorrect border value: {border_value}\n")
        error_report.append(f"❌ Incorrect border value: {border_value}\n")
    else:
        full_report.append(f"💚 Correct border value: 0\n")
    
    if error_report:
        error_report.insert(0,f"Line number: {src_line}\n")
        error_report.insert(0,f"🏞️  Image\n")
        error_report.append('\n')
    full_report.append('\n')


    return full_report,error_report
    
def check_query_params(tag,utm_campaign):

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
        error_report.insert(0,f"Line number: {tag.sourceline}\n")
        error_report.insert(0,f"🔗 Link {href}\n")
        error_report.append('\n')
    full_report.append('\n')

    return full_report, error_report
    
def check_frag_id(tag,anchor_tags_with_name):
    error_report = []
    full_report =[]
    href=tag['href']

    if href[1:] in anchor_tags_with_name:
        full_report.append(f"🔎 Fragment Identifier:\nLine number: {tag.sourceline}\n💚 {href[1:]} ref found in file\n\n")
    else:
        error_report.append(f"🔎 Fragment Identifier:\nLine number: {tag.sourceline}\n❌ {href[1:]} ref not found in file\n\n")
    
    return full_report, error_report

def check_html_file(file, utm_campaign):
        
    soup = BeautifulSoup(file, 'html.parser')
    anchor_img_tags = soup.find_all(['a','img'])
    anchor_tags_with_name = [tag.attrs['name'] for tag in anchor_img_tags if 'name' in tag.attrs]
    
    full_report_parts = []
    error_report_parts = []
    
    for tag in anchor_img_tags:
        if tag.name=='a':
            if 'href' in tag.attrs.keys():
                href = tag['href']
                if href.startswith('#'):
                    full_report_tag, error_report_tag = check_frag_id(tag,anchor_tags_with_name=anchor_tags_with_name)

                    full_report_parts.extend(full_report_tag)
                    
                    if error_report_tag:
                        error_report_parts.extend(error_report_tag)
                else:
                    # here full report and error report are multiple parts to extend to main lists
                    full_report_params, error_report_params = check_query_params(tag=tag,utm_campaign=utm_campaign)
                    
                    full_report_parts.extend(full_report_params)
                    if error_report_params:
                        error_report_parts.extend(error_report_params)
        else:
            # here full report and error report are multiple parts to extend to main lists
            full_report_img, error_report_img = check_image_attributes(image_tag=tag) 
            full_report_parts.extend(full_report_img)
            
            if error_report_img:
                error_report_parts.extend(error_report_img)
        

    return ''.join(full_report_parts), ''.join(error_report_parts)
    
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
      
def send_error_message(client: SocketModeClient, channel, thread_ts, error_message):
    try:
        client.web_client.chat_postMessage(
                channel=channel,
                text=error_message,
                thread_ts=thread_ts
            )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def verify_input(utm_campaign, files):
    # utm campaign = "text"
    if not utm_campaign: 
        return True, ERROR_INVALID_UTM_MISSING
    elif " " in utm_campaign:
        return True, ERROR_INVALID_UTM_FORMAT
    elif not files:
        return True, ERROR_FILE_NOT_FOUND
    elif len(files)>1:
        return True, ERROR_FILE_MULTIPLE
    elif not files[0]['filetype'] == 'html':
        return True, ERROR_FILE_NOT_HTML
    else:
        return False, None

def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        event = req.payload["event"]
        # Acknowledge the request anyway
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)
        channel = event["channel"]

        # Check if it's a message event (excluding bot messages)
        if event["type"] == "message" and "bot_id" not in event and channel == EMAIL_QA_AUTOMATION_CHANNEL_ID:

            # This message is the first in the channel, not a response to a thread
            thread_ts = event.get('thread_ts', event['ts']) 
            if thread_ts == event['ts']:
            
                utm_campaign = event.get('text', '').strip()  
                files = event.get('files', [])

                error_flag, error_message = verify_input(utm_campaign, files)

                if error_flag:
                    send_error_message(client, channel, thread_ts, error_message)
                else:
                    file_url = files[0]['url_private']

                    headers = {
                        "Authorization": f"Bearer {slack_api_token}"
                    }

                    file_response = requests.get(file_url, headers=headers)
                    
                    if file_response.status_code == 200:
                        html_content = file_response.text

                        full_report, error_report = check_html_file(html_content,utm_campaign)

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
                        send_error_message(client, channel, thread_ts, ERROR_FILE_HTTP_REQUEST + file_response.text + ERROR_NEW_REQUEST_PROMPT)
            else:
                # This is a response to an existing thread
                send_error_message(client, channel, thread_ts, ERROR_NEW_REQUEST_PROMPT)
          

                         

client.socket_mode_request_listeners.append(process)
# Establish a WebSocket connection to the Socket Mode servers
client.connect()

# Do not stop this process
from threading import Event
Event().wait()
