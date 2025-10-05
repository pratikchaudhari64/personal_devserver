import time
import asyncio
from typing import Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

# --- Simulated Ollama Chat (Non-blocking I/O) ---
class SimulatedOllamaChat:
    # ... (ainvoke implementation remains the same) ...
    async def ainvoke(self, prompt: str, simulated_delay: float) -> str:
        start_time = time.perf_counter()
        # This await yields control, freeing the event loop for other user requests
        await asyncio.sleep(simulated_delay) 
        end_time = time.perf_counter()
        return (
            f"Response for '{prompt[:20]}...' | "
            f"Inference time: {end_time - start_time:.2f}s"
        )
ollamachat = SimulatedOllamaChat()

# --- Data Structure for a Single Request ---
class SingleChatRequest(BaseModel):
    prompt: str
    simulated_delay: float = 2.0 # Default delay

app = FastAPI(title="Real-Time Concurrent Chat App")

# --- The Generate Response Function (A separate task) ---
async def generate_llm_response(prompt: str, delay: float) -> str:
    # This function is where the non-blocking I/O occurs
    return await ollamachat.ainvoke(prompt, delay)


# --- The FastAPI Endpoint ---
@app.post("/chat")
async def handle_single_chat(request: SingleChatRequest) -> Dict[str, Any]:
    """
    Handles a single user request, initiates the LLM call, and waits ONLY 
    for that specific result before returning.
    
    Other concurrent requests hitting this same endpoint will run in parallel 
    because of the 'await' inside generate_llm_response.
    """
    request_start_time = time.perf_counter()
    
    print(f"\n[Server] Request received for: '{request.prompt[:20]}...'")
    
    # 1. Initiate the LLM call and await its result.
    # When this await is hit, the function yields, allowing other users 
    # to hit the server and start their own tasks concurrently.
    response_content = await generate_llm_response(
        request.prompt, 
        request.simulated_delay
    )

    request_end_time = time.perf_counter()
    
    return {
        "prompt": request.prompt,
        "response": response_content,
        "total_user_wait_time": round(request_end_time - request_start_time, 2)
    }

# To run this: uvicorn main:app --reload