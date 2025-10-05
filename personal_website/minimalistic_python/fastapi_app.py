# app.py (FastAPI Version)

import asyncio
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ollama_bot import bot_start, generate_llm_response # <-- Reused!

# --- SETUP ---
app = FastAPI()

# Mount static files (like your CV and assets)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templating (assuming your templates are in 'templates' folder)
templates = Jinja2Templates(directory="templates")


# 1. Startup Hook: Uses FastAPI's native event to run bot_start once
# @app.on_event("startup")
# def startup_event():
#     print("Starting up FastAPI application...")
    
bot_start()

# --- Blocking HTML Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home"})

@app.get("/projects", response_class=HTMLResponse)
async def projects(request: Request):
    return templates.TemplateResponse("projects.html", {"request": request, "title": "Projects"})

@app.get("/blog", response_class=HTMLResponse)
async def blog(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request, "title": "Blog"})

@app.get("/cv")
async def cv():
    # FileResponse handles this natively
    return FileResponse('static/cv.pdf', filename='PratikChaudhari_cv.pdf', media_type='application/pdf')


# --- Asynchronous LLM Route (The Key Benefit) ---

@app.post("/chat-cv")
async def chatcv(request: Request):
    # Get the question from request (using FastAPI's awaitable request.json())
    try:
        data = await request.json()
        question = data.get('question', '')
    except:
        return JSONResponse(content={"answer": "Invalid JSON format."}, status_code=400)
    
    # print(f"question: {question}")
    
    try:
        # Await the asynchronous LLM call
        LLM_resp = await generate_llm_response(question)
    except Exception as e:
        print(f"LLM Error: {e}")
        LLM_resp = "Sorry, the LLM service is temporarily unavailable."
        # Use FastAPI's JSONResponse with status code
        return JSONResponse(content={"answer": LLM_resp}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    # Return a standard Python dictionary, FastAPI converts it to JSON automatically
    return {"answer": LLM_resp}

# --- Execution Command (Terminal Only) ---
# You would run this from the terminal, not inside the if __name__ block:
# uvicorn app:app --host 0.0.0.0 --port 3001 --reload