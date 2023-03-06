FROM public.ecr.aws/lambda/python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY utils ${LAMBDA_TASK_ROOT}/utils
COPY app.py ${LAMBDA_TASK_ROOT}

RUN ls ${LAMBDA_TASK_ROOT}

RUN python -m nltk.downloader -d /usr/share/nltk_data punkt && python -m nltk.downloader -d /usr/share/nltk_data stopwords
RUN python -m nltk.downloader -d /usr/local/share/nltk_data punkt && python -m nltk.downloader -d /usr/local/share/nltk_data stopwords

ENTRYPOINT [ "python" ]

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.py" ]