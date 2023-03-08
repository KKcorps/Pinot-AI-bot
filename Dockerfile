FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .

# Streamlit needs to be installed seperately because it doesn't work properly when installed in LAMBDA_TASK_ROOT
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}" && pip3 install streamlit 

# Copy function code, Not copying everything as it will copy the virtual env as well.
COPY utils ${LAMBDA_TASK_ROOT}/utils
COPY app.py ${LAMBDA_TASK_ROOT}
COPY ui.py ${LAMBDA_TASK_ROOT}
COPY .env ${LAMBDA_TASK_ROOT}

RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt stopwords averaged_perceptron_tagger

EXPOSE 8501

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.handle_slack_command_lamda" ]