import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Initialize a Slack API client with a user token
client = WebClient(token=os.environ["SLACK_API_KEY"])

MAX_MESSAGES_COUNT = 10

## returns list of slack conversation with similar question: list[str]
def search_slack(query):
    slack_convos = []
    # Call the search.messages API method with the query parameter
    try:
        response = client.search_messages(query=query)
        messages = response["messages"]["matches"]
        print(f"Found {len(messages)} messages matching the search query:")
        for message in messages:
            print(message)
            slack_convos.append(messages["text"])
            if len(slack_convos) > MAX_MESSAGES_COUNT:
                break
    except SlackApiError as e:
        print(f"Error: {e}")
    return slack_convos

