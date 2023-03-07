# Pinot-AI-bot


You need to add the following environment variables before running

* GITHUB_API_KEY
* OPEN_AI_KEY
* SLACK_WEBHOOK_URL
* SLACK_API_KEY
* GITBOOK_API_KEY
* SNS_TOPIC_NAME - in case deplying on Lambda
* SNS_TOPIC_REGION - in case deplying on Lambda

If you want to use the docker image, add the previous env variables in a `.env` file in the root directory besides `app.py`.