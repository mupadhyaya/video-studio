import os
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain import hub

# Secure your API keys in environment variables
os.environ["TAVILY_API_KEY"] = "tvly-your-production-key-here"
os.environ["OPENAI_API_KEY"] = "sk-proj-your-key-here"

def initialize_web_search_agent():
    # Define the LLM with tool-calling capabilities
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    # Instantiate the Tavily Search Tool optimized for LLM consumption
    search_tool = TavilySearchResults(max_results=2)
    tools = [search_tool]
    
    # Pull standard system prompt from LangChain Hub
    prompt = hub.pull("hwchase17/openai-tools-agent")
    
    # Construct the agent state machine and executor runner
    agent = create_openai_tools_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return executor