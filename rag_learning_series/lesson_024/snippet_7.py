from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import uvicorn

# Initialize FastAPI application
app = FastAPI(
    title="Production Agentic RAG API Service",
    description="High-performance API engine powered by asynchronous agentic routing pipelines.",
    version="1.0.0"
)

# Instantiate core orchestrator
agent_orchestrator = AgentOrchestrator()

class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    status: str
    response_text: str

@app.post(
    "/api/v1/agent/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Agentic Query Pipeline"
)
async def handle_agent_query(payload: QueryRequest):
    try:
        if not payload.prompt.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User prompt cannot be empty or whitespaces."
            )
        
        # Non-blocking execution of agentic search pipeline
        result = await agent_orchestrator.process_query(payload.prompt)
        return QueryResponse(status="success", response_text=result)
        
    except Exception as err:
        print(f"[Critical System Error] {str(err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal routing failed: {str(err)}"
        )

if __name__ == '__main__':
    # Run production async server locally
    uvicorn.run(app, host="127.0.0.1", port=8000)