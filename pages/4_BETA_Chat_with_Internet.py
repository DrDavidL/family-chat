import streamlit as st
import requests
from loguru import logger
import trafilatura
from trafilatura import bare_extraction
import os
import queue
import re
import tempfile
import threading
import pandas as pd


from embedchain import App as I_app
from embedchain.config import BaseLlmConfig
from embedchain.helpers.callbacks import (StreamingStdOutCallbackHandlerYield,
                                          generate)

i_app = I_app()

def create_table_from_text(text):
    """ Example function to detect, extract, and format table-like data. More complex implementations might be necessary. """
    # Placeholder function body; real implementation will depend on actual text structures
    # data = {
    #     "Study and Design": ["ATLAS53 RCT, Superiority", "Ward et al54 RCT, Superiority"],
    #     "No. enrolled": [446, 344],
    #     "Outcome point": ["3 mo", "6 mo"],
    #     "Primary Outcome": ["Success", "Success"]
    # }
    df = pd.DataFrame(text)
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

def get_ec_app(api_key):
    if "i_app" in st.session_state:
        print("Found app in session state")
        i_app = st.session_state.i_app
    else:
        print("Creating app")
        db_path = get_db_path()
        i_app = embedchain_bot(db_path, api_key)
        st.session_state.i_app = i_app
    return i_app

def embedchain_bot(db_path, api_key):
    return I_app.from_config(
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
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
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
@st.cache_data
def realtime_search(query, domains, max):
    url = "https://real-time-web-search.p.rapidapi.com/search"
    
    # Combine domains and query
    full_query = f"{domains} {query}"
    querystring = {"q": full_query, "limit": max}

    headers = {
        "X-RapidAPI-Key": st.secrets["X-RapidAPI-Key"],
        "X-RapidAPI-Host": "real-time-web-search.p.rapidapi.com",
    }

    urls = []
    snippets = []

    try:
        response = requests.get(url, headers=headers, params=querystring)
        
        # Check if the request was successful
        if response.status_code == 200:
            response_data = response.json()
            # st.write(response_data.get('data', []))
            for item in response_data.get('data', []):
                urls.append(item.get('url'))   
                snippets.append(f"**{item.get('title')}**  \n*{item.get('snippet')}*  \n{item.get('url')} <END OF SITE>")

        else:
            st.error(f"Search failed with status code: {response.status_code}")
            return [], []

    except requests.exceptions.RequestException as e:
        st.error(f"RapidAPI real-time search failed to respond: {e}")
        return [], []

    return snippets, urls

def extract_url_content(url):
    logger.info(url)
    downloaded = trafilatura.fetch_url(url)
    content =  trafilatura.extract(downloaded)

    # logger.info(url +"______"+  content)
    return {"url":url, "content":content}

st.title("📄 Chat with Internet!")

st.warning("Not fully working yet! Try at your peril! :)")
if "messages_web" not in st.session_state:
    st.session_state.messages_web = [
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

if check_password():
    openai_access_token = st.secrets["OPENAI_API_KEY"]
    st.session_state.api_key = openai_access_token
    all_site_text = []
    if "search_results" not in st.session_state:
        st.session_state["search_results"] = []
    site_number = st.number_input("Number of sites", min_value=1, max_value=10, value=5, step=1)    
    initial_search = st.text_input("Enter search query")
    if st.button("Search"):
        initial_response, urls = realtime_search(initial_search, "all", site_number)
        with st.expander("Source URLs:"):
            st.write(urls)
        for site in urls:
            try:
                i_app.add(site, data_type='web_page')
                
            except Exception as e:
                st.error(f"Error adding {site}: {e}, skipping that one!")
            # st.write(f'here is a site: {site}')
        #     site_text = extract_url_content(site)
        #     all_site_text.append(site_text)
        # with st.expander("All Site Text:"):
        #     st.write(all_site_text)
        
    for message in st.session_state.messages_web:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything!"):
        if not st.session_state.api_key:
            st.error("Please enter your OpenAI API Key", icon="🤖")
            st.stop()

        i_app = get_ec_app(st.session_state.api_key)

        with st.chat_message("user"):
            st.session_state.messages_web.append({"role": "user", "content": prompt})
            st.markdown(prompt)

        with st.chat_message("assistant"):
            msg_placeholder = st.empty()
            msg_placeholder.markdown("Thinking...")
            full_response = ""

            q = queue.Queue()

            def app_response(result):
                llm_config = i_app.llm.config.as_dict()
                llm_config["callbacks"] = [StreamingStdOutCallbackHandlerYield(q=q)]
                config = BaseLlmConfig(**llm_config)
                answer, citations = i_app.query(prompt, config=config, citations=True)
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
            st.write(f' here are the full {citations}')
            
            refine_output(citations)
            msg_placeholder.markdown(full_response)
            # print("Answer: ", full_response)
            st.session_state.messages_web.append({"role": "assistant", "content": full_response})
    
    # app = App()
    data_sources = i_app.get_data_sources()

    st.sidebar.write("Files in database: ", len(data_sources))
    for i in range(len(data_sources)):
        full_path = data_sources[i]["data_value"]
        # Extract just the filename from the full path
        temp_filename = os.path.basename(full_path)
        # Use regex to only keep up to the first .pdf in the filename
        cleaned_filename = re.sub(r'^(.+?\.pdf).*$', r'\1', temp_filename)
        st.sidebar.write(i, ": ", cleaned_filename)


            
    if st.sidebar.button("Clear database (click twice to confirm)"):
        i_app = I_app()
        i_app.reset()
    
    if st.session_state.messages_web:    
        if st.sidebar.button("Clear chat history."):
            st.session_state["messages_web"] = []
        