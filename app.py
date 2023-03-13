import sys
from utils.process_query import generate_response
import requests

from flask import Flask, request, Response
from threading import Thread
import re
import os
import json
import base64
from requests_toolbelt.multipart import decoder
from urllib.parse import parse_qs
import boto3
from dotenv import load_dotenv
load_dotenv(override=True)


app = Flask(__name__)

WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "foo_bar")
MY_SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_NAME", "foo_bar")
SNS_TOPIC_REGION = os.environ.get("SNS_TOPIC_REGION", "foo_bar")
APP_PORT = int(os.environ.get("APP_PORT", "8080"))

headers = {'Content-type': 'application/json'}
is_sns_client_init = False
sns_client = None
if "SNS_TOPIC_REGION" in os.environ:
    sns_client = boto3.client('sns', region_name=SNS_TOPIC_REGION)
    is_sns_client_init = True

def format_slack_text(text):
    text = re.sub(r'\n+', '\n', text)
    return text
    # text = text.replace("```", " ")
    # return "```" + text + "```"

def append_question(text, query):
    return f"*{query}* {text}"

def get_response(query):
    answer = generate_response(query)
    return append_question(format_slack_text(answer), query)

def handle_slack(query, response_url = None):
    slack_response = {"text": get_response(query)}
    if response_url is None or response_url == "":
        requests.post(WEBHOOK_URL, json=slack_response, headers=headers)
    else:
        requests.post(response_url, json=slack_response, headers=headers)

@app.route('/')
def home():
    return "Pinot AI Bot is alive!!"

@app.route("/ask", methods=['POST'])
def ask_ai_command():
    data = request.form
    query = data.get("text")
    response_url = data.get("response_url")
    if query is None or len(query) == 0:
        print("No query provided!")
        slack_response = {"text": format_slack_text("No query provided")}
        if response_url is None:
            response_url = WEBHOOK_URL
        requests.post(response_url, json=slack_response, headers=headers)
        return Response("No query provied"), 400
    #TODO: do not create a new thread for every request obviously   
    if "SLACK_WEBHOOK_URL" in os.environ:
        Thread(target = handle_slack, args=[query, response_url]).start()
        return Response(f"Queued: *{query}*. We now let AI cook!"), 200
    else:
        return Response(f"{get_response(query)}"), 200


def handle_sns_command_lamda(event, context):
    message = json.loads(event['Records'][0]['Sns']['Message'])
    query = message['text']
    response_url = message['response_url']
    handle_slack(query, response_url)
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "data ": f"Query Processed: *{query}*. Check slack for response!"
        })
    }
    return response

def handle_slack_command_lamda(event, context):
    print(f"JSON EVENT RECEIVED: {json.dumps(event)}")
    query = ""
    response_webhook_url = ""
    if "body" in event:
        isBase64 = False
        if "isBase64Encoded" in event:
            isBase64 = event.get("isBase64Encoded")
        request_body = event.get("body")
        if isBase64:
            content_type = event.get("headers").get("Content-Type")
            decoded_body = base64.b64decode(request_body)
            form_data = decoder.MultipartDecoder(decoded_body, content_type)
            part = form_data.parts[0]
            query = part.text
            if "response_url" in part:
                response_webhook_url = part.response_url
        else:
            content_type = event.get("headers").get("Content-Type")
            if "urlencoded" in content_type:
                parsed_request = parse_qs(request_body)
                query = parsed_request.get("text")[0]
                if "response_url" in parsed_request:
                    response_webhook_url = parsed_request.get("response_url")[0]
            else:
                json_body = json.loads(request_body)
                query = json_body.get("text")
                if "response_url" in json_body:
                    response_webhook_url = json_body.get("response_url")
    else:
        query = event.get("text")
        if "response_url" in event:
            response_webhook_url = event.get("response_url")
    
    if query is None or len(query) == 0:
        print("No query provided!")
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "text/plain"
            },
            "body": "No Query Provided"
        }
        return response
    
    message = {"text": query, "response_url": response_webhook_url}

    ## SNS is required because the API calls generally timeout when using via SLACK bot
    ## So you return the response immediately and let the second handle_sns_command_lamda 
    ## do all the processing after receiving the message from SNS topic
    if is_sns_client_init:
        sns_response = sns_client.publish(
                TopicArn=MY_SNS_TOPIC_ARN,
                Message=json.dumps({'default': json.dumps(message)}),
                MessageStructure='json'
            )
    
    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/plain"
        },
        "body": f"Queued: *{query}*. Please wait for max 60 seconds while AI cooks the answer!"
    }
    return response



def run():
  app.run(host='0.0.0.0',port=APP_PORT)

def serve():
    from waitress import serve
    serve(app, host="0.0.0.0", port=APP_PORT)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        serve()
    else:
        keep_alive()
