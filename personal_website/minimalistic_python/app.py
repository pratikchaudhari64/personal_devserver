from flask import Flask, render_template, request, jsonify, send_from_directory
import time
import asyncio
from ollama_bot import bot_start, generate_llm_response

bot_start()

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html", title="Home")

@app.route("/projects")
def projects():
    return render_template("projects.html", title="Projects")

@app.route("/blog")
def blog():
    return render_template("blog.html", title="Blog")

@app.route("/cv")
def cv():
    return send_from_directory('static', 'cv.pdf', as_attachment=True, download_name='PratikChaudhari_cv.pdf')

@app.route("/chat-cv", methods=['POST'])
async def chatcv():
    # Get the question from request (optional, for later use)
    data = request.get_json()
    question = data.get('question', '')
    
    # Your LLM response (placeholder for now)
    print(f"question: {question}")
    try:
        LLM_resp = await generate_llm_response(question)
    except Exception as e:
        print(f"LLM Error: {e}")
        LLM_resp = "Sorry, the LLM service is temporarily unavailable."
        return jsonify({"answer": LLM_resp}), 503
    
    # Return JSON response as expected by JavaScript
    return jsonify({"answer": LLM_resp})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
    # app.run(debug=True, host="0.0.0.0", port = 3001)
    
    pass
