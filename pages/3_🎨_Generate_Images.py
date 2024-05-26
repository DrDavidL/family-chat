# imports.py
# Grouping imports for clarity and better organization

# Standard library imports
import os
import io

# Third-party library imports
import requests
import streamlit as st
from PIL import Image
from openai import OpenAI

# Local imports
from prompts import improve_image_prompt
from embedchain import App

# constants.py
# Constants for the application

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_URL = "https://api.openai.com/v1/images/generations"

# utils.py
# Utility functions for the application

def fetch_openai_client():
    return OpenAI(base_url="https://api.openai.com/v1", api_key=OPENAI_API_KEY)

def better_image_prompt(initial_prompt: str, system_prompt: str) -> str:
    client = fetch_openai_client()
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f'user prompt: {initial_prompt}'}
        ]
    )
    return response.choices[0].message.content

def download_image(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    else:
        st.error("Failed to download image.")
        return None

def generate_image(prompt: str, model: str = 'dall-e-2', n: int = 1, quality: str = 'standard', response_format: str = 'url', size: str = '1024x1024', style: str = 'vivid', user: str = None):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "model": model,
        "n": n,
        "quality": quality,
        "response_format": response_format,
        "size": size,
        "style": style,
    }
    if user:
        payload["user"] = user
    
    response = requests.post(OPENAI_URL, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error generating image: {response.text}")
        return None

# main.py
# Main application logic

if "final_prompt" not in st.session_state:
    st.session_state["final_prompt"] = ""

st.title('🎨 OpenAI DALL·E Image Generator')

if st.session_state.get("password_correct", False):

    prompt = st.text_area("Enter a prompt for the image", max_chars=4000)
    
    with st.sidebar:
        model = st.selectbox("Model", ['dall-e-2', 'dall-e-3'], index=0)
        n = st.number_input("Number of images (1-10)", min_value=1, max_value=10, value=1, step=1) if model == 'dall-e-2' else 1
        
        with st.expander("Advanced Options"):
            quality = st.selectbox("Quality", ['standard', 'hd'], index=0)
            response_format = 'url'
            size = st.selectbox("Size", ['256x256', '512x512', '1024x1024'] if model == 'dall-e-2' else ['1024x1024', '1792x1024', '1024x1792'], index=0)
            style = st.selectbox("Style", ['vivid', 'natural'], index=0)
            user = st.text_input("User Identifier (optional)")

    if st.button("Improve my prompt"):
        improved_prompt = better_image_prompt(prompt, improve_image_prompt)
        st.session_state.final_prompt = st.text_area("Edit as needed", value=improved_prompt, height=100)
        
    if st.checkbox("Use Original Prompt"):
        st.session_state.final_prompt = prompt
        
    if st.button("Generate Image"):
        result = generate_image(st.session_state.final_prompt, model, n, quality, response_format, size, style, user)
        if result:
            images = result.get('data', [])
            for i, image in enumerate(images):
                url = image.get("url")
                img = download_image(url)
                if img:
                    st.image(img, caption="Generated Image")
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    st.download_button(
                        label="Download Image",
                        data=img_byte_arr.getvalue(),
                        file_name=f"generated_img_{i+1}.png",
                        mime="image/png"
                    )
    if st.session_state.final_prompt:
        with st.expander("Prompt Used"):
            st.write(st.session_state.final_prompt)
else:
    st.warning("Please return to the Main page to enter your password.")
