import os
import requests
import streamlit as st
from PIL import Image
import io

# Assuming your OpenAI API Key is stored in an environment variable
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
OPENAI_URL = "https://api.openai.com/v1/images/generations"

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
def download_image(url):
    response = requests.get(url)
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    else:
        st.error("Failed to download image.")
        return None
def generate_image(prompt, model='dall-e-2', n=1, quality='standard', response_format='url', size='1024x1024', style='vivid', user=None):
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

st.title('OpenAI DALL·E Image Generator')

if check_password():

    prompt = st.text_area("Enter a prompt for the image", max_chars=4000)
    model = st.selectbox("Model", ['dall-e-2', 'dall-e-3'], index=0)
    if model == 'dall-e-2':
        n = st.number_input("Number of images (1-10)", min_value=1, max_value=10, value=1, step=1)
    else:
        n = 1
    quality = st.selectbox("Quality", ['standard', 'hd'], index=0)
    response_format = 'url'
    # response_format = st.selectbox("Response Format", ['url', 'b64_json'], index=0)
    size = st.selectbox("Size", ['256x256', '512x512', '1024x1024'] if model == 'dall-e-2' else ['1024x1024', '1792x1024', '1024x1792'], index=0)
    style = st.selectbox("Style", ['vivid', 'natural'], index=0)
    user = st.text_input("User Identifier (optional)")

    if st.button("Generate Image"):
        result = generate_image(prompt, model, n, quality, response_format, size, style, user)
        if result:
            images = result.get('data', [])
            for i, image in enumerate(images):
                url = image.get("url")
                img = download_image(url)
                if img:
                    st.image(img, caption="Generated Image")
                    # Converts the image object to bytes again for downloading
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    st.download_button(
                        label="Download Image",
                        data=img_byte_arr.getvalue(),
                        file_name=f"generated_img_{i+1}.png",
                        mime="image/png"
                    )
