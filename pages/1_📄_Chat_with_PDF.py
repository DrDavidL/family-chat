import os
import queue
import re
import tempfile
import threading
import pandas as pd

import streamlit as st

from embedchain import App
from embedchain.config import BaseLlmConfig
from embedchain.helpers.callbacks import (StreamingStdOutCallbackHandlerYield,
                                          generate)
# __import__('pysqlite3')
import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

def create_table_from_text(text):
    """ Example function to detect, extract, and format table-like data. More complex implementations might be necessary. """
    # Placeholder function body; real implementation will depend on actual text structures
    data = {
        "Study and Design": ["ATLAS53 RCT, Superiority", "Ward et al54 RCT, Superiority"],
        "No. enrolled": [446, 344],
        "Outcome point": ["3 mo", "6 mo"],
        "Primary Outcome": ["Success", "Success"]
    }
    df = pd.DataFrame(data)
    return df.to_string(index=False)  # Returns a string that represents the DataFrame in table form.

def clean_text(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = text.replace('-', ' ').replace(' .', '.')
    text = re.sub(r"\s{2,}", " ", text)  # Replace multiple spaces with a single space
    return text

def refine_output(data):
    with st.expander("Source Excerpts:"):
        for text, info in sorted(data, key=lambda x: x[1]['score'], reverse=True)[:3]:
            st.write(f"Score: {info['score']}\n")
            cleaned_text = clean_text(text)
            
            # if "Table" in cleaned_text:
            #     st.write("Extracted Table:")
            #     st.write(create_table_from_text(cleaned_text))  # Example of integrating table extraction
            # else:
            st.write("Text:\n", cleaned_text)
            st.write("\n")

# def clean_text(text):
#     """ Insert spaces before capital letters to reconstruct sentences, handle special characters. """
#     text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # Space before capital letters
#     text = text.replace('-', ' ').replace(' .', '.')  # Replace dashes, correct spacings before periods
#     return text

def process_data(data):
    # Sort the data based on the score in descending order and select the top three
    top_three = sorted(data, key=lambda x: x[1]['score'], reverse=True)[:3]
    
    # Format each text entry
    for text, info in top_three:
        cleaned_text = clean_text(text)
        st.write(f"Score: {info['score']}\nText: {cleaned_text}\n")

if st.session_state.messages_web:
    app = App()
    app.reset()
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            app = App()
            app.reset()
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        # random_number = random.randint(1000000000, 9999999999)
        st.text_input(
            "Password", type="password", on_change=password_entered, key='password'
        )
        st.write("*Please contact David Liebovitz, MD if you need an updated password for access.*")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True
def embedchain_bot(db_path, api_key):
    return App.from_config(
        config={
            "llm": {
                "provider": "openai",
                "config": {
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.5,
                    "max_tokens": 4000,
                    "top_p": 1,
                    "stream": True,
                    "api_key": api_key,
                },
            },
            "vectordb": {
                "provider": "chroma",
                "config": {"collection_name": "chat-pdf", "dir": db_path, "allow_reset": True},
            },
            "embedder": {"provider": "openai", "config": {"api_key": api_key}},
            "chunker": {"chunk_size": 2000, "chunk_overlap": 0, "length_function": "len"},
        }
    )


def get_db_path():
    tmpdirname = tempfile.mkdtemp()
    return tmpdirname


def get_ec_app(api_key):
    if "app" in st.session_state:
        print("Found app in session state")
        app = st.session_state.app
    else:
        print("Creating app")
        db_path = get_db_path()
        app = embedchain_bot(db_path, api_key)
        st.session_state.app = app
    return app
st.title("📄 Chat with PDFs!")
# st.warning("Before using - clear the database on left sidebar! I'm working to make sure it starts empty! ")

if check_password():

    with st.sidebar:
        # openai_access_token = st.text_input("OpenAI API Key", key="api_key", type="password")
        # "WE DO NOT STORE YOUR OPENAI KEY."
        # "Just paste your OpenAI API key here and we'll use it to power the chatbot. [Get your OpenAI API key](https://platform.openai.com/api-keys)"  # noqa: E501
        openai_access_token = st.secrets["OPENAI_API_KEY"]
        st.session_state.api_key = openai_access_token

        if st.session_state.api_key:
            app = get_ec_app(st.session_state.api_key)

        pdf_files = st.file_uploader("Upload your PDF files", accept_multiple_files=True, type="pdf")
        st.write("File Upload history only ⬆️. Section below shows current files in the knowledge base⬇️.")
        add_pdf_files = st.session_state.get("add_pdf_files", [])
        for pdf_file in pdf_files:
            file_name = pdf_file.name
            if file_name in add_pdf_files:
                continue
            try:
                if not st.session_state.api_key:
                    st.error("Please enter your OpenAI API Key")
                    st.stop()
                temp_file_name = None
                with tempfile.NamedTemporaryFile(mode="wb", delete=False, prefix=file_name, suffix=".pdf") as f:
                    f.write(pdf_file.getvalue())
                    temp_file_name = f.name
                if temp_file_name:
                    st.markdown(f"Adding {file_name} to knowledge base...")
                    app.add(temp_file_name, data_type="pdf_file")
                    st.markdown("")
                    add_pdf_files.append(file_name)
                    os.remove(temp_file_name)
                st.session_state.messages_pdf.append({"role": "assistant", "content": f"Added {file_name} to knowledge base!"})
            except Exception as e:
                st.error(f"Error adding {file_name} to knowledge base: {e}")
                st.stop()
        st.session_state["add_pdf_files"] = add_pdf_files

    
    # styled_caption = '<p style="font-size: 17px; color: #aaa;">🚀 An <a href="https://github.com/embedchain/embedchain">Embedchain</a> app powered by OpenAI!</p>'  # noqa: E501
    # st.markdown(styled_caption, unsafe_allow_html=True)

    if "messages_pdf" not in st.session_state:
        st.session_state.messages_pdf = [
            # {
            #     "role": "system",
            #     "content": """You answer questions about PDF documents. You provide two sections in your response.\n
            #     ## Response Using PDF Content\n
            #     ...
            #     ## Response Commentary from a domain specific AI expert\n """,
            # },
            {
                "role": "assistant",
                "content": """
                    Hi! I'm chatbot that answers questions about your pdf documents.\n
                    Upload your pdf documents here and I'll answer your questions about them! 
                """,
            }
        ]

    for message in st.session_state.messages_pdf:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything!"):
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API Key", icon="🤖")
            st.stop()

        app = get_ec_app(st.session_state.api_key)

        with st.chat_message("user"):
            st.session_state.messages_pdf.append({"role": "user", "content": prompt})
            st.markdown(prompt)

        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            msg_placeholder.markdown("Thinking...")
            full_response = ""

            q = queue.Queue()

            def app_response(result):
                llm_config = app.llm.config.as_dict()
                llm_config["callbacks"] = [StreamingStdOutCallbackHandlerYield(q=q)]
                config = BaseLlmConfig(**llm_config)
                answer, citations = app.query(prompt, config=config, citations=True)
                result["answer"] = answer
                result["citations"] = citations
                

            results = {}
            thread = threading.Thread(target=app_response, args=(results,))
            thread.start()

            for answer_chunk in generate(q):
                full_response += answer_chunk
                msg_placeholder.markdown(full_response)

            thread.join()
            answer, citations = results["answer"], results["citations"]
            if citations:
                full_response += "\n\n**Sources**:\n"
                sources = []
                for i, citation in enumerate(citations):
                    source = citation[1]["url"]
                    pattern = re.compile(r"([^/]+)\.[^\.]+\.pdf$")
                    match = pattern.search(source)
                    if match:
                        source = match.group(1) + ".pdf"
                    sources.append(source)
                sources = list(set(sources))
                for source in sources:
                    full_response += f"- {source}\n"
            # st.write(f' here are the full {citations}')
            
            refine_output(citations)
            msg_placeholder.markdown(full_response)
            # print("Answer: ", full_response)
            st.session_state.messages_pdf.append({"role": "assistant", "content": full_response})
    
    # app = App()
    data_sources = app.get_data_sources()

    st.sidebar.write("Files in database: ", len(data_sources))
    for i in range(len(data_sources)):
        full_path = data_sources[i]["data_value"]
        # Extract just the filename from the full path
        temp_filename = os.path.basename(full_path)
        # Use regex to only keep up to the first .pdf in the filename
        cleaned_filename = re.sub(r'^(.+?\.pdf).*$', r'\1', temp_filename)
        st.sidebar.write(i, ": ", cleaned_filename)


            
    if st.sidebar.button("Clear database (click twice to confirm)"):
        app = App()
        app.reset()
    
    if st.session_state.messages_pdf:    
        if st.sidebar.button("Clear chat history."):
            st.session_state["messages_pdf"] = []

# @misc{embedchain,
#   author = {Taranjeet Singh, Deshraj Yadav},
#   title = {Embedchain: The Open Source RAG Framework},
#   year = {2023},
#   publisher = {GitHub},
#   journal = {GitHub repository},
#   howpublished = {\url{https://github.com/embedchain/embedchain}},
# }