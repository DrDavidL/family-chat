# app.py
import streamlit as st
from openai import OpenAI
import random
import json
import markdown2
import requests
import datetime
import pytz

from prompts import system_prompt_regular, system_prompt_essayist, system_prompt_expert
from embedchain import App
from groq import Groq


# Streamlit page configuration
st.set_page_config(page_title='Family Chat', layout='centered', page_icon=':stethoscope:', initial_sidebar_state='expanded')

# Initialize session states
for key in ["response", "messages", "full_conversation", "summarized"]:
    if key not in st.session_state:
        st.session_state[key] = "" if key == "response" else [] if key in ["messages", "full_conversation"] else False

# Function to parse Groq stream data
def parse_groq_stream(stream):
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# Function to summarize messages with a language model
def summarize_messages_with_llm(model, messages, char_limit=1000):
    # Filter out system messages and join user messages into a single string
    conversation_to_summarize = " ".join(msg["content"] for msg in messages if msg["role"] != "system")
    
    # Check if there is any conversation to summarize
    if not conversation_to_summarize:
        return "No content to summarize."
    
    # Prepare the request for summarization
    summary_request_messages = [
        {"role": "system", "content": "Summarize the following conversation:"},
        {"role": "user", "content": conversation_to_summarize}
    ]
    
    # Attempt to summarize the conversation
    try:
        with st.spinner("Summarizing conversation..."):
            summary_response = llm_call(model, summary_request_messages, stream=False)
            summarized_response = f"Conversation summarized for brevity: {summary_response}"
            if len(summary_response) > char_limit:
                summary_response = summary_response[:char_limit] + "..."
            st.session_state.summarized = True
            return summarized_response
    except requests.exceptions.RequestException as req_err:
        st.error(f"Request error during summarization: {req_err}")
        return "Failed to summarize due to a request error."
    except json.JSONDecodeError as json_err:
        st.error(f"JSON decode error during summarization: {json_err}")
        return "Failed to summarize due to a JSON decode error."
    except Exception as e:
        st.error(f"Unexpected error during summarization: {e}")
        return "Failed to summarize due to an unexpected error."

# Function to enforce length constraints with summarization
def enforce_length_constraint_with_summarization(model, messages, max_tokens=7000, system_role="system"):
    # Calculate the maximum allowable length of messages
    max_length = max_tokens * 4
    # Compute the total length of all messages
    total_length = sum(len(message["content"]) for message in messages)
    
    # Check if the total length exceeds the maximum length
    if total_length > max_length:
        try:
            # Separate messages based on their role
            system_messages = [message for message in messages if message["role"] == system_role]
            user_messages = [message for message in messages if message["role"] != system_role]
            
            # Summarize the user messages to reduce total length
            summarized_content = summarize_messages_with_llm(model, user_messages)
            
            # Combine system messages with the summarized user messages
            reduced_messages = system_messages + [{"role": "user", "content": summarized_content}]
            return reduced_messages
        except requests.exceptions.RequestException as req_err:
            st.error(f"Request error during summarization: {req_err}")
            return messages
        except json.JSONDecodeError as json_err:
            st.error(f"JSON decode error during summarization: {json_err}")
            return messages
        except Exception as e:
            st.error(f"Unexpected error during summarization: {e}")
            return messages
    
    # Return original messages if within length constraints
    return messages

def set_client(model):
    # Define the API keys and base URLs for different clients
    clients = {
        "llama3-70b-8192": Groq(api_key=st.secrets["GROQ_API_KEY"]),
        "gpt-4o": OpenAI(base_url="https://api.openai.com/v1", api_key=st.secrets["OPENAI_API_KEY"]),
        "gpt-3.5-turbo": OpenAI(base_url="https://api.openai.com/v1", api_key=st.secrets["OPENAI_API_KEY"]),
        "gpt-4-turbo": OpenAI(base_url="https://api.openai.com/v1", api_key=st.secrets["OPENAI_API_KEY"]),
    }
    # Return the appropriate client or default to OpenRouter API
    client = clients.get(model)
    if client is None:
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=st.secrets["OPENROUTER_API_KEY"])
    return client
    

from typing import List, Dict, Any

def llm_call(model: str, messages: List[Dict[str, Any]], stream: bool = True) -> str:
    try:
        # Set the appropriate client based on the model
        client = set_client(model)
        # Create a completion request with the language model
        completion = client.chat.completions.create(
            model=model, 
            messages=messages, 
            temperature=0.5, 
            max_tokens=1000, 
            stream=stream
        )
        if stream:
            # Initialize an empty response string and a Streamlit placeholder for streaming output
            full_response = ""
            placeholder = st.empty()
            # Iterate through the streamed chunks of responses
            for chunk in completion:
                # Check if there is content to add to the full response
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    # Update the placeholder with the current full response
                    placeholder.markdown(full_response)
            return full_response
        else:
            # Return the full response content when not streaming
            return completion.choices[0].message.content
    except requests.exceptions.RequestException as req_err:
        st.error(f"Request error during LLM call: {req_err}")
        return "Failed to get response due to a request error."
    except json.JSONDecodeError as json_err:
        st.error(f"JSON decode error during LLM call: {json_err}")
        return "Failed to get response due to a JSON decode error."
    except Exception as e:
        st.error(f"Unexpected error during LLM call: {e}")
        return "Failed to get response due to an unexpected error."

# Function to check user password
def check_password() -> bool:
    def password_entered() -> None:
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            app = App()
            app.reset()
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    st.session_state.setdefault("password_correct", False)
    if not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key='password')
        st.write("*Please contact David Liebovitz, MD if you need an updated password for access.*")
        return False

    if not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False

    return True

# Main Streamlit app layout and functionality
st.title("💬 Family Chat")

if check_password():
    global system
    system = ""

    def display_sidebar(system):
        st.title('Customization')
        st.session_state.model = st.selectbox("Model Options", (
            "anthropic/claude-3-haiku", "llama3-70b-8192", "anthropic/claude-3-sonnet",
            "anthropic/claude-3-opus", "gpt-4o", "gpt-3.5-turbo", "gpt-4-turbo", 
            "google/gemini-pro", "google/gemini-pro-1.5", "meta-llama/llama-3-70b-instruct:nitro"), index=4)
        
        prompt_options = {
            "Revise and improve an essay": system_prompt_essayist,
            "Regular user": system_prompt_regular,
            "Expert Answers": system_prompt_expert
        }
        
        pick_prompt = st.radio("Pick a personality", list(prompt_options.keys()), index=1)
        system = st.sidebar.text_area("Make your own system prompt or use as is:", value=prompt_options[pick_prompt], height=100)
        
        if not st.session_state.messages:
            central_tz = pytz.timezone('US/Central')
            timestamp = datetime.datetime.now(central_tz).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.messages.append({"role": "system", "content": f'Note user likely location (Chicago) date and time:[{timestamp}] {system}'})
        
        if st.button("Update Personality"):
            central_tz = pytz.timezone('US/Central')
            timestamp = datetime.datetime.now(central_tz).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.messages.append({"role": "system", "content": f'Note user likely location (Chicago) date and time:[{timestamp}] Ignore prior guidance and use this system prompt: {system}'})

    st.info("Type your questions at the bottom of the page!")
    with st.sidebar:
        display_sidebar(system)

    # Display conversation history
    for message in st.session_state.full_conversation:
        avatar = "👩‍⚕️" if message["role"] == "user" else "🤓"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Accept user input and process it
    if prompt := st.chat_input("What's up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.full_conversation.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👩‍⚕️"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤓"):
            try:
                st.session_state.messages = enforce_length_constraint_with_summarization(st.session_state.model, st.session_state.messages)
                response = llm_call(st.session_state.model, st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.full_conversation.append({"role": "assistant", "content": response})
                st.session_state.response = response
            except Exception as e:
                st.error(f"Error: {e}")

    # Offer download option for the conversation
    if st.session_state.full_conversation:
        conversation_str = "\n\n".join(
            f"👩‍⚕️: {msg['content']}" if msg["role"] == "user" else f"🤓: {msg['content']}"
            for msg in st.session_state.full_conversation
        )
        html = markdown2.markdown(conversation_str, extras=["tables"])
        st.download_button('Download the conversation', html, f'conversation.html', 'text/html')

    # Sidebar options to clear chat memory
    if st.sidebar.button("Clear chat memory (click twice to confirm)"):
        st.session_state["messages"] = [{"role": "system", "content": system}]
        st.sidebar.info("Chat memory cleared and ready to start new conversation!")
    
    if st.sidebar.button("Clear recorded conversation and memory (click twice to confirm)"):
        st.session_state["messages"] = [{"role": "system", "content": system}]
        st.session_state["full_conversation"] = []
        st.sidebar.info("Full history cleared and ready to start new conversation!")

    if st.session_state.summarized:
        st.sidebar.warning("The conversation has been summarized. Please start a new conversation if earlier details needed.")
