# Install necessary libraries
pip install langchain-openai python-dotenv

# Set your OpenAI API key as an environment variable
# For example, in your terminal before running Python:
# export OPENAI_API_KEY="sk-...your-openai-api-key-here"

# Or within Python (for local testing, not recommended for production):
# from dotenv import load_dotenv
# import os
# load_dotenv() # take environment variables from .env.
# openai_api_key = os.getenv("OPENAI_API_KEY")
