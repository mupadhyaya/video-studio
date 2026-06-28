import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Securely load the API key from system environment variables
api_key = os.getenv("OPENAI_API_KEY", "default-fallback-key")

# Configure components with specific parameters
prompt = ChatPromptTemplate.from_template("Tell me a brief professional joke about {topic}.")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, openai_api_key=api_key)
parser = StrOutputParser()

# Construct the LCEL pipe architecture
chain = prompt | model | parser

if __name__ == "__main__":
    # Execute the synchronous invocation of our chain
    result = chain.invoke({"topic": "software engineering"})
    print(f"Chain Output:\n{result}")