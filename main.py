import streamlit as st
from prompts import *
import markdown2
from openai import OpenAI
import requests
import json
import random

import random

# Generate a random 10-digit number


st.set_page_config(page_title='Family Chat', layout = 'centered', page_icon = ':stethoscope:', initial_sidebar_state = 'expanded')

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

def enforce_length_constraint_with_summarization(model, messages, max_length=7000, system_role="system"):
    """
    Enforces maximum length constraint on messages with the ability to summarize using llm_call.
    
    Parameters:
        model (str): Model identifier for summarization.
        messages (list of dict): The list of messages in the conversation.
        max_length (int): Maximum allowed length for all messages combined.
        system_role (str): Role identifier for system messages which are to be left intact.
        
    Returns:
        list of dict: Adjusted list of messages that comply with the max_length constraint.
    """
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
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + st.secrets["OPENROUTER_API_KEY"],  # Fixed to correct access to secrets
            "Content-Type": "application/json",
            "HTTP-Referer": "https://fsm-gpt-med-ed.streamlit.app",  # To identify your app
            "X-Title": "lof-sims",
        },
        data=json.dumps({
            "model": model,
            "messages": messages,
        })
    )
    # Extract the response content
    response_data = response.json()
    return response_data # Adjusted to match expected JSON structure


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



st.title("Family Chat")



if check_password():
    st.info("Type your questions at the bottom of the page!")

    with st.sidebar:
        st.title('Customization')
        st.session_state.model = st.selectbox("Model Options", ("anthropic/claude-3-haiku",
        "anthropic/claude-3-sonnet", "anthropic/claude-3-opus", "openai/gpt-3.5-turbo", "openai/gpt-4-turbo", 
        "google/gemini-pro", "google/gemini-pro-1.5","meta-llama/llama-3-70b-instruct:nitro", ), index=0)
        pick_prompt = st.radio("Pick a prompt", ("Revise and improve an essay", "Regular user", "Expert Answers", "Other"), index=1)
        if pick_prompt == "Revise and improve an essay":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_essayist, height=300)
        elif pick_prompt == "Regular user":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_regular, height=300)
        elif pick_prompt == "Expert Answers":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_expert, height=300)
        elif pick_prompt == "Other":
            system = st.sidebar.text_area("Make your own system prompt or use as is:", value=system_prompt_regular, height=300)
        
        st.info("Note - selecting a new prompt may impact the chat memory! Default is Regular User. Download anything you wanted to save first.")    
        if st.button("Update system prompt"):
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
        with st.spinner("Thinking..."):
            try:
                response = llm_call(st.session_state.model, st.session_state.messages)
            except Exception as e:
                st.error(f"Error (Call Dad or re-start the app): {e}")
                st.stop()
        response = response['choices'][0]['message']['content']
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.full_conversation.append({"role": "assistant", "content": response})
        with st.chat_message("assistant", avatar="🤓"):        
            st.session_state.response = st.write(response)
    
                
    

    if st.session_state["full_conversation"]:
        conversation_str = ""
        for message in st.session_state.full_conversation:
            if message["role"] == "user":
                conversation_str += "👩‍⚕️: " + message["content"] + "\n\n"
            elif message["role"] == "assistant":
                conversation_str += "🤓: " + message["content"] + "\n\n"
        html = markdown2.markdown(conversation_str, extras=["tables"])
        st.download_button('Download the conversation when done!', html, f'response.html', 'text/html')
    
    if st.sidebar.checkbox("Clear chat history"):
        st.session_state["messages"] = [{"role": "system", "content": system}]
        st.sidebar.info("Chat history cleared and ready to start new conversation!")
        
 