import asyncio
from langchain_ollama import ChatOllama
from typing import Optional

# 1. Declare the variable globally (initially None)
# Use Optional[] for type hinting since it starts as None
ollamachatllm: Optional[ChatOllama] = None 

def bot_start():
    """Initializes the Ollama client and sets the global variable."""
    global ollamachatllm 
    
    try:
        # Create the ChatOllama client
        llm_client = ChatOllama(
            model="gemma3:4b",
            validate_model_on_init=True,
            temperature=0.8,
            num_predict=256,
            # other params ...
        )
        # Assign it to the global variable
        ollamachatllm = llm_client
        print("✅ Ollama Chat Client initialized successfully.")

    except Exception as e:
        print(f"❌ Error occurred during Ollama client initialization: {e}")
        # Optionally re-raise the error or exit the program if this is critical
        raise RuntimeError("Ollama service not accessible. Check if server is running.") from e

async def generate_llm_response(prompt: str) -> str:
    """Handles asynchronous calls to the Ollama server."""
    
    if not ollamachatllm:
        raise RuntimeError("Ollama client has not been initialized. Call bot_start() first.")
    
    response = await ollamachatllm.ainvoke(prompt)
    
    return response.content if hasattr(response, 'content') else str(response)