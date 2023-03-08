FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY utils ${LAMBDA_TASK_ROOT}/utils
COPY app.py ${LAMBDA_TASK_ROOT}
COPY .env ${LAMBDA_TASK_ROOT}

RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt stopwords averaged_perceptron_tagger

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.handle_slack_command_lamda" ]