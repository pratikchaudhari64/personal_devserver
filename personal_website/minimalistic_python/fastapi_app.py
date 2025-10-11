# app.py (FastAPI Version)

import asyncio
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
import sys

gunicorn_logger = logging.getLogger('gunicorn.error')
root_logger = logging.getLogger() 

if gunicorn_logger.handlers:
    root_logger.handlers = [] 
    root_logger.handlers.extend(gunicorn_logger.handlers)
    root_logger.setLevel(gunicorn_logger.level) 

# from ollama_bot import bot_start, generate_llm_response # <-- Reused!
from gemini import RAG

# --- SETUP ---
app = FastAPI()

# Mount static files (like your CV and assets)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templating (assuming your templates are in 'templates' folder)
templates = Jinja2Templates(directory="templates")

    
# bot_start()
SECRET_PATH = "/run/secrets/gemini_api_key"
rag = RAG(GEMINI_EMBED_MODEL="gemini-embedding-001",
          CHAT_MODEL_NAME="gemini-2.5-flash-lite",
          API_KEY=open(SECRET_PATH, 'r').read())

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
        # LLM_resp = await generate_llm_response(question)
        LLM_resp = await rag.generate_with_retrieved_docs(query=question)
    except Exception as e:
        print(f"LLM Error: {e}")
        LLM_resp = "Sorry, the LLM service is temporarily unavailable."
        # Use FastAPI's JSONResponse with status code
        return JSONResponse(content={"answer": LLM_resp}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    # Return a standard Python dictionary, FastAPI converts it to JSON automatically
    return {"answer": LLM_resp}
