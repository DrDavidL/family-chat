
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


### Image Analysis Tool

Employs advanced image recognition techniques to analyze uploaded images, giving insights or descriptions about the content of the image which can be particularly useful for educational or accessibility purposes.


## Getting Started - For General Use

To run this application locally, you'll need to have Python and Pip installed on your system. Follow the steps below to set up the environment and start the application:

1. Clone the repository to your local machine:

```bash
git clone https://github.com/drdavidl/family-chat/blob/main/main.py
```

2. Navigate to the project directory:

```bash
cd path-to-your-project
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

Also, be sure to copy the secrets.example file into a secrets.toml file (within the .streamlit directory) that is **NOT** tracked by git. This file should contain your API keys and a password so only shared users can access it. (Individual accounts when I have time...).

4. Start the Streamlit application:

```bash
streamlit run main.py
```

## For Contributors

If you're considering contributing to the project, please start by forking the repository. This will create your own copy of the project under your account, where you can make changes without affecting the original codebase.

After forking, you can clone your forked repository to your local environment using:

```bash
git clone https://your-forked-repository-url.git
```

From there, you can create a new branch for your changes, commit those changes, and push them back to your forked repository. When you're ready, submit a pull request to propose integrating your changes into the original project.
```

## Usage

Follow the on-screen instructions for each feature within the Streamlit application. Here's a brief overview:

- **Chatbot with Memory**: Engage with the chatbot through the chat interface. The chatbot will remember context from your conversation for a seamless experience.
- **PDF Chat Feature**: Upload PDF documents through the provided interface. You can then ask the chatbot questions related to the content of the uploaded documents.
- **Image Generation**: Enter a textual prompt describing the image you wish to generate, and the application will use AI to create an image based on your description.
- **Image Analysis**: Upload an image to have it analyzed by our AI tool. The application will provide information or an interpretation of the image's content.

## Acknowledgments

- Chatbot feature powered by [OpenRouter API](https://openrouter.ai).
- Image generation built with technologies from [OpenAI](https://openai.com).
- Image analysis utilizes advanced computer vision models, also from OpenAI.

## References

We make use of the Embedchain framework in this project:

- Taranjeet Singh, Deshraj Yadav. Embedchain: The Open Source RAG Framework. 2023, GitHub. Available at: [https://github.com/embedchain/embedchain](https://github.com/embedchain/embedchain).

<a href="https://www.buymeacoffee.com/dlteach" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

[![Buy Me A Coffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/dlteach)
