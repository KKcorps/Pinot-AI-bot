from utils.process_query import generate_response
import logging
import streamlit as st
import streamlit.components.v1 as components
import time
from dotenv import load_dotenv
load_dotenv(override=True)

# Configure logger
logging.basicConfig(format="\n%(asctime)s\n%(message)s", level=logging.INFO, force=True)

import nltk
nltk.download("stopwords")
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")

# Define functions
def generate_text():
    if not query:
        return
    logging.info(query)

    if len(query) == 0:
        st.session_state.text_error = "Have you considered typing something?"
        return

    if st.session_state.n_requests >= 10:
        st.session_state.text_error = "Too many requests. Please wait a few seconds before generating another Tweet."
        logging.info(f"Session request limit reached: {st.session_state.n_requests}")
        st.session_state.n_requests = 1
        return

    result = generate_response(query)

    # st.session_state.response = result.response
    st.session_state.answer = result
    st.session_state.text_error = ""
    st.session_state.n_requests += 1
    st.session_state.response_loading = False


# Configure Streamlit page and state
st.set_page_config(page_title="Pinot AI Bot", page_icon="🤖")

if "text_error" not in st.session_state:
    st.session_state.text_error = ""
if "n_requests" not in st.session_state:
    st.session_state.n_requests = 0
# if "response" not in st.session_state:
#     st.session_state.response = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "response_loading" not in st.session_state:
    st.session_state.response_loading = False


# Force responsive layout for columns also on mobile
st.write(
    """<style>
    [data-testid="column"] {
        width: calc(50% - 1rem);
        flex: 1 1 calc(50% - 1rem);
        min-width: calc(50% - 1rem);
    }
    </style>""",
    unsafe_allow_html=True,
)

# Render Streamlit page
st.title("Pinot AI")
st.markdown(
    "Shoot me a dm [@khare_khote](https://twitter.com/khare_khote) if it breaks, or you want to sponsor credits."
)


query = st.text_input(label="What do you want to know about Pinot?")
if st.session_state.text_error:
    st.warning(st.session_state.text_error)

st.button(label="Ask", on_click=generate_text)

if st.session_state.answer:
    if "Sorry" not in st.session_state.answer:
        st.success("Found Answer!")

if st.session_state.answer:
    if "Sorry" not in st.session_state.answer:
        st.header("Is this what you're looking for?")
    st.markdown(st.session_state.answer)