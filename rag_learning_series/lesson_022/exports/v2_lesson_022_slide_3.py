from llama_index.multi_modal_llms.openai import OpenAIMultiModal

# Initialize GPT-4o as our Multimodal Engine
multi_modal_llm = OpenAIMultiModal(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

query_engine = index.as_query_engine(multi_modal_llm=multi_modal_llm)
response = query_engine.query("What is the trend shown in chart_1?")