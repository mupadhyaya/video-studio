import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Ensure your OPENAI_API_KEY is set as an environment variable
# e.g., export OPENAI_API_KEY="sk-..."

# 1. Define the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 2. Define the Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant. Respond concisely."),
    ("user", "{topic}")
])

# 3. Define the Output Parser
output_parser = StrOutputParser()

# 4. Create the Chain using LCEL
chain = prompt | llm | output_parser

# 5. Invoke the Chain with an input
response = chain.invoke({"topic": "tell me a fun fact about space"})

# 6. Print the response
print(response)