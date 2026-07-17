import base64
from openai import OpenAI
import json

client = OpenAI()

def encode_image_to_base64(image_path):
    """Converts any local image into base64 format for API transport."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def summarize_visual_chart(image_path):
    """Extracts data and generates a structural description of charts using GPT-4o."""
    base64_image = encode_image_to_base64(image_path)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this image in detail. Extract all key performance metrics, axis values, and patterns. Return the results strictly as a JSON object containing keys: 'summary', 'extracted_metrics', and 'trends'."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)