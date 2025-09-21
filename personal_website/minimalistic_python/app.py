from flask import Flask, render_template, request, jsonify, send_from_directory
import time

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
def chatcv():
    # Get the question from request (optional, for later use)
    data = request.get_json()
    question = data.get('question', '')
    
    # Your LLM response (placeholder for now)
    print(f"question: {question}")
    LLM_resp = "hello, this is response from the LLM"
    
    # Return JSON response as expected by JavaScript
    return jsonify({"answer": LLM_resp})


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port = 3001)
    pass
