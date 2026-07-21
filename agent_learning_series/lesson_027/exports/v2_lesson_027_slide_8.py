# Mock execution function
def get_stock_price(ticker: str, interval: str = "1d") -> dict:
    # In a real app, this would query a real financial API
    return {"ticker": ticker, "price": 182.50, "currency": "USD", "interval": interval}

# Simulated parsing and execution logic
tool_call_from_model = {
    "name": "get_stock_price",
    "arguments": '{"ticker": "AAPL", "interval": "1d"}'
}

# Dynamic Execution
if tool_call_from_model["name"] == "get_stock_price":
    args = json.loads(tool_call_from_model["arguments"])
    execution_result = get_stock_price(**args)
    
    # Formulating the Tool Message to return to the LLM
    tool_message = {
        "role": "tool",
        "tool_call_id": "call_abc123",
        "name": "get_stock_price",
        "content": json.dumps(execution_result)
    }
    print(json.dumps(tool_message, indent=2))