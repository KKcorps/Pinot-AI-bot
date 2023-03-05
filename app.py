import sys
from utils.process_query import generate_response
import requests

from flask import Flask, request, Response
from threading import Thread
import re
import os
# from keep_alive import keep_alive

app = Flask(__name__)

WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
headers = {'Content-type': 'application/json'}

def format_slack_text(text):
    text = re.sub(r'\n+', '\n', text) 
    return "```" + text + "```"

def append_question(text, query):
    return f"*{query}* {text}"

def handle_slack(query):
    answer = generate_response(query)
    slack_response = {"text": append_question(format_slack_text(answer), query)}
    requests.post(WEBHOOK_URL, json=slack_response, headers=headers)


@app.route('/')
def home():
    return "Pinot AI Bot is alive!!"

@app.route("/ask", methods=['POST'])
def ask_ai_command():
    data = request.form
    query = data.get("text")
    if query is None:
        print("No query provided!")
        slack_response = {"text": format_slack_text("No query provided")}
        requests.post(WEBHOOK_URL, json=slack_response, headers=headers)
        return Response(), 400
    #TODO: do not create a new thread for every request obviously   
    Thread(target = handle_slack, args=[query]).start()
    return Response(f"Queued: *{query}*. We now let AI cook!"), 200

def handle_slack_command_lamda(event, context):
    query = event.get("text")
    if query is None or len(query) == 0:
        print("No query provided!")
        response = {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "data ": "No query provied"
            })
        }
        return response
    handle_slack(query)
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



def run():
  app.run(host='0.0.0.0',port=9003)

def keep_alive():
    t = Thread(target=run)
    t.start()
