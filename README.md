
# Project Title: API Powered AI Chatbot

This application leverates cutting-edge AI technologies to offer a comprehensive suite of features, including a conversational chatbot with memory capabilities, a PDF chat feature for document-based interactions, image generation powered by OpenAI, and an advanced image analysis tool. 

## Features

### Chatbot with Memory Using OpenRouter

Utilizes the OpenRouter API (for a variety of models) to provide an intelligent chatbot experience that can remember context from previous interactions, making conversations more coherent and engaging.

![Chatbot with Memory](path/to/chatbot_memory_screenshot.png)

### PDF Chat Feature Using Embedchain

Leverages the Embedchain library to facilitate document-based chats. Users can upload PDF documents, and the chatbot can reference content within these documents to provide relevant responses.

![PDF Chat Feature](path/to/pdf_chat_feature_screenshot.png)

### Image Generation with OpenAI

Integrates with OpenAI's API to generate images based on textual prompts provided by users. This feature harnesses the power of models like DALL-E to transform creative ideas into visual art.

![Image Generation](path/to/image_generation_screenshot.png)

### Image Analysis Tool

Employs advanced image recognition techniques to analyze uploaded images, giving insights or descriptions about the content of the image which can be particularly useful for educational or accessibility purposes.

![Image Analysis Tool](path/to/image_analysis_tool_screenshot.png)

## Getting Started

To run this application locally, you'll need to have Python and Pip installed on your system. Follow the steps below to set up the environment and start the application:

1. Clone the repository to your local machine:

```bash
git clone https://your-repository-url.git
```

2. Navigate to the project directory:

```bash
cd path-to-your-project
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Start the Streamlit application:

```bash
streamlit run app.py
```

## Usage

Follow the on-screen instructions for each feature within the Streamlit application. Here's a brief overview:

- **Chatbot with Memory**: Engage with the chatbot through the chat interface. The chatbot will remember context from your conversation for a seamless experience.
- **PDF Chat Feature**: Upload PDF documents through the provided interface. You can then ask the chatbot questions related to the content of the uploaded documents.
- **Image Generation**: Enter a textual prompt describing the image you wish to generate, and the application will use AI to create an image based on your description.
- **Image Analysis**: Upload an image to have it analyzed by our AI tool. The application will provide information or an interpretation of the image's content.

## Acknowledgments

- Chatbot feature powered by [OpenRouter API](https://openrouter.ai).
- PDF chat functionality provided by [Embedchain](https://github.com/embedchain/embedchain). 
  ```bibtex
  @misc{embedchain,
    author = {Taranjeet Singh, Deshraj Yadav},
    title = {Embedchain: The Open Source RAG Framework},
    year = {2023},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\url{https://github.com/embedchain/embedchain}},
  }
  ```
- Image generation built with technologies from [OpenAI](https://openai.com).
- Image analysis utilizes advanced computer vision models.

Please replace the `"path/to/..."` placeholders with the actual paths to your screenshots, and adjust the repository URL and other specifics according to your project's details.


## References

We make use of the Embedchain framework in this project:

- Taranjeet Singh, Deshraj Yadav. Embedchain: The Open Source RAG Framework. 2023, GitHub. Available at: [https://github.com/embedchain/embedchain](https://github.com/embedchain/embedchain).
