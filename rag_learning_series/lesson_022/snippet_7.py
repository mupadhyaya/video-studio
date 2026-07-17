def run_multimodal_rag(query):
    """Queries the vector store, fetches original context images, and generates synthesized answer."""
    # Query vector database
    results = vectorstore.similarity_search_with_relevance_scores(query, k=1)
    if not results or results[0][1] < 0.6:
        return "No highly relevant source data found matching query."
        
    best_match_doc = results[0][0]
    element_id = best_match_doc.metadata["element_id"]
    
    # Retrieve actual source image
    retrieved_image = image_document_store[element_id]
    
    # Synthesize structured response using Vision LLM
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Based on the visual chart and metadata provided, answer this query: {query}. Metadata Context: {best_match_doc.page_content}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{retrieved_image}"
                        }
                    }
                ]
            }
        ]
    )
    return response.choices[0].message.content