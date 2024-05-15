import streamlit as st
from prompts import *
import markdown2
from openai import OpenAI
import requests
import json
import random
from groq import Groq
groq_client = Groq(api_key = st.secrets['GROQ_API_KEY'])
# __import__('pysqlite3')
import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from embedchain import App

# Generate a random 10-digit number


st.set_page_config(page_title='Family Chat', layout = 'centered', page_icon = ':stethoscope:', initial_sidebar_state = 'expanded')

def parse_groq_stream(stream):
    for chunk in stream:
        if chunk.choices:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
def summarize_messages_with_llm(model, messages):
    """
    Uses the llm_call function to summarize older conversations.
    
    Parameters:
        model (str): Model identifier for making API calls.
        messages (list of dict): The messages to summarize.

    Returns:
        str: Summarized content as a string.
    """
    # Combine messages into a single string for summarization
    conversation_to_summarize = " ".join([msg["content"] for msg in messages if msg["role"] != "system"])
    
    # Creating a placeholder for the summarized response
    summarized_response = "Conversation summarized for brevity."
    
    with st.spinner("Summarizing conversation..."):
        if conversation_to_summarize:
            try:
                summary_request_messages = [
                    {"role": "system", "content": "Summarize the following conversation:"},
                    {"role": "user", "content": conversation_to_summarize}
                ]
                summary_response = llm_call(model, summary_request_messages)
                if summary_response and 'choices' in summary_response and len(summary_response['choices']) > 0:
                    summarized_response = summary_response['choices'][0]['message']['content']
            except Exception as e:
                print(f"Error during summarization with llm_call: {e}")
    
    return summarized_response

def enforce_length_constraint_with_summarization(model, messages, max_tokens=7000, system_role="system"):
    max_length = max_tokens * 4  # Approximate character limit based on token limit
    total_length = sum(len(message["content"]) for message in messages)
    
    if total_length > max_length:
        # Separating system messages and other messages
        system_messages = [message for message in messages if message["role"] == system_role]
        other_messages = [message for message in messages if message["role"] != system_role]
        
        # Use llm_call to summarize these messages
        summarized_content = summarize_messages_with_llm(model, other_messages)
        
        # Reconstructing the messages list
        reduced_messages = system_messages + [{"role": "user", "content": summarized_content}]
        
        return reduced_messages

    return messages


def llm_call(model, messages):
    api_key = st.secrets["OPENROUTER_API_KEY"]
    client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    completion = client.chat.completions.create(
        model = model,
        messages = messages,
        # headers={ "HTTP-Referer": "https://fsm-gpt-med-ed.streamlit.app", # To identify your app
        #     "X-Title": "GPT and Med Ed"},
        temperature = 0.5,
        max_tokens = 1000,
        stream = True,   
        )
    

    placeholder = st.empty()
    full_response = ''
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
            # full_response.append(chunk.choices[0].delta.content)
            placeholder.markdown(full_response)
    placeholder.markdown(full_response)
    return full_response


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



st.title("💬 Family Chat")



if check_password():
    st.info("Type your questions at the bottom of the page!")

    with st.sidebar:
        st.title('Customization')
        st.session_state.model = st.selectbox("Model Options", ("anthropic/claude-3-haiku", "groq-fast-llama3",
        "anthropic/claude-3-sonnet", "anthropic/claude-3-opus", "gpt-4o", "openai/gpt-3.5-turbo", "openai/gpt-4-turbo", 
        "google/gemini-pro", "google/gemini-pro-1.5","meta-llama/llama-3-70b-instruct:nitro", ), index=1)
        st.info("Choose personality, edit as needed, and click update personality below.")    
        pick_prompt = st.radio("Pick a personality", ("Revise and improve an essay", "Regular user", "Expert Answers", ), index=1)
        if pick_prompt == "Revise and improve an essay":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_essayist, height=100)
        elif pick_prompt == "Regular user":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_regular, height=100)
        elif pick_prompt == "Expert Answers":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_expert, height=100)
        elif pick_prompt == "Other":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_regular, height=100)
        
        
        if st.button("Update Personality"):
            st.session_state.messages += [{"role": "system", "content": f'Ignore prior guidance and use this system prompt: {system}'}]
            
            
            
            
        
        # Initialize chat history

        
    # if st.sidebar.checkbox("Change personality? (Will clear history.)"):
    #     persona = st.sidebar.radio("Pick the persona", ("Regular user", "Physician"), index=1)
    #     if persona == "Regular user":
    #         system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt2)
    #     else:
    #         system = system_prompt
    #     st.session_state.messages = [{"role": "system", "content": system}]
        
    if "response" not in st.session_state:
        st.session_state["response"] = ""

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": system}]
        
    if "full_conversation" not in st.session_state:
        st.session_state["full_conversation"] = []
        
  

            # Audio selection
    

    for message in st.session_state.full_conversation:
        if message["role"] == "user":
            with st.chat_message(message["role"], avatar="👩‍⚕️"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message(message["role"], avatar="🤓"):
                st.markdown(message["content"])




    
# Accept user input
    if prompt := st.chat_input("What's up?"):
        # Add user message to chat history
        # Assuming you've selected a model in your Streamlit app.
        model_id = st.session_state.model

        # Enforce length constraint and summarize if necessary
        st.session_state.messages =  enforce_length_constraint_with_summarization(model_id, st.session_state.messages)

        # # Proceed with the regular llm_call
        # response = llm_call(model_id, st.session_state.messages)

        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.full_conversation.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user", avatar="👩‍⚕️"):
            st.markdown(prompt)
            
            # Display assistant response in chat message container
        # with st.spinner("Thinking..."):
        #     try:
        #         stream = llm_call(st.session_state.model, st.session_state.messages)
        #     except Exception as e:
        #         st.error(f"Error (Call Dad or re-start the app): {e}")
        #         st.stop()

        with st.chat_message("assistant", avatar="🤓"): 
            if st.session_state.model == "groq-fast-llama3":            
                stream = groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                temperature=0.5,
                stream=True,
                )
                response = st.write_stream(parse_groq_stream(stream))
            elif st.session_state.model == "gpt-4o":
                api_key = st.secrets["OPENAI_API_KEY"]
                client = OpenAI(
                        base_url="https://api.openai.com/v1",
                        api_key=api_key,
                )
                completion = client.chat.completions.create(
                    model = st.session_state.model,
                    messages = st.session_state.messages,
                    # headers={ "HTTP-Referer": "https://fsm-gpt-med-ed.streamlit.app", # To identify your app
                    #     "X-Title": "GPT and Med Ed"},
                    temperature = 0.5,
                    max_tokens = 1000,
                    stream = True,   
                    )     
            
                # placeholder = st.empty()
                response =st.write_stream(completion)
                
            else:
                api_key = st.secrets["OPENROUTER_API_KEY"]
                client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key,
                    )
                completion = client.chat.completions.create(
                    model = st.session_state.model,
                    messages = st.session_state.messages,
                    # headers={ "HTTP-Referer": "https://fsm-gpt-med-ed.streamlit.app", # To identify your app
                    #     "X-Title": "GPT and Med Ed"},
                    temperature = 0.5,
                    max_tokens = 1000,
                    stream = True,   
                    )     
            
                # placeholder = st.empty()
                response =st.write_stream(completion)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.full_conversation.append({"role": "assistant", "content": response})
            st.session_state.response = response
    
                
    

    # if st.session_state["full_conversation"]:
    if st.session_state.response:
        conversation_str = ""
        for message in st.session_state.full_conversation:
            if message["role"] == "user":
                conversation_str += "👩‍⚕️: " + message["content"] + "\n\n"
            elif message["role"] == "assistant":
                conversation_str += "🤓: " + message["content"] + "\n\n"
        html = markdown2.markdown(conversation_str, extras=["tables"])
        st.download_button('Download the conversation when done!', html, f'response.html', 'text/html')
    
    if st.sidebar.button("Clear chat memory. (Leaves Conversation intact for downloading still.) (click twice to confirm)"):
        st.session_state["messages"] = [{"role": "system", "content": system}]
        st.sidebar.info("Chat memory cleared and ready to start new conversation!")
        
    if st.sidebar.button("Clear recorded conversation and memory. (click twice to confirm)"):
        st.session_state["messages"] = [{"role": "system", "content": system}]
        st.sidebar.info("Full history cleared and ready to start new conversation!")
        st.session_state["full_conversation"] = []
        
 