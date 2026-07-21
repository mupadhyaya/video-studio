from pydantic import BaseModel, Field
from openai import OpenAI
import json

# Define the schema using Pydantic
class GetStockPrice(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol, e.g. AAPL, MSFT")
    interval: str = Field("1d", description="Time interval for historical data: 1m, 5m, 1d")

# Representing the tool for OpenAI API
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Retrieve historical stock price data for a given ticker.",
            "parameters": GetStockPrice.model_json_schema()
        }
    }
]

# Print the underlying JSON schema generated
print(json.dumps(tools, indent=2))