import streamlit as st
import base64
import requests
from PIL import Image
import io

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
def encode_image(uploaded_file):
    # Convert the uploaded file to an image
    image = Image.open(uploaded_file)
    
    # Determine the image format
    img_format = 'PNG' if image.format == 'PNG' else 'JPEG'
    
    # Convert the image to bytes
    buffer = io.BytesIO()
    image.save(buffer, format=img_format)
    encoded_string = base64.b64encode(buffer.getvalue()).decode()
    
    # Properly format the base64 string for HTTP transmission
    data_uri = f"data:image/{img_format.lower()};base64,{encoded_string}"
    return data_uri

def analyze_image(data_uri):
    api_key = st.secrets["OPENAI_API_KEY"]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image? If the image is a question or problem, apply a careful process creating an overall plan and then applying step by step processes to solve or answer the question or problem."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error from OpenAI: {response.text}")
        return None

st.title("Image Analyzer (and more!)")

if check_password():

    uploaded_file = st.file_uploader("Upload a JPEG or PNG image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Display the uploaded image
        st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
        # Convert to base64 for API call
        data_uri = encode_image(uploaded_file)
        
        if st.button("Analyze Image"):
            with st.spinner("Analyzing..."):
                result = analyze_image(data_uri)
                
                # Displaying the response
                if result:
                    responses = result.get('choices', [])
                    if responses:
                        response_text = responses[0].get('message', {}).get('content', '')
                        st.write("Analysis Result:", response_text)
                    else:
                        st.write("No analysis result found.")
