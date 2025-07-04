from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from notion_api import get_markdown

# Create a FastAPI application instance
app = FastAPI()

@app.get('/')
async def home():
    """
    Root endpoint for the Notion application.
    Returns a welcome message.
    """

    return JSONResponse(content={"message": "Hello from Notion App (FastAPI)!"}, status_code = 200)

@app.get('/page/{page_id}')
async def get_notion_page_markdown(page_id: int):
    """
    Retrieves the entire Markdown content of a Notion page by its ID.
    """
    # if not NOTION_API_KEY:
    #     raise HTTPException(status_code=500, detail="Notion API key not configured.")

    
    # markdown_content = get_markdown(page_id)
    # print(markdown_content)
    try:
        markdown_content = get_markdown(page_id)
        # Return as PlainTextResponse with Markdown media type
        return Response(content=markdown_content, media_type="text/markdown")
    # except HTTPException as e:
    #     # Re-raise HTTPExceptions from the helper function
    #     raise e
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    


# @app.get('/health')
# async def health_check():
#     """
#     Health check endpoint.
#     Used by Docker Compose to determine if the service is ready.
#     """
#     return JSONResponse(content={"status": "healthy"}, status_code=200)


if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=5000)

    pass