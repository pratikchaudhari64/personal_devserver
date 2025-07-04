# Personal Web Server & Project Showcase

Host multiple web projects from your local machine via one public URL using **Docker**, **Nginx**, and a **tunneling tool** (like ngrok).

## Quick Setup

1.  **Clone & Run Docker:**
    ```bash
    git clone [https://github.com/your-username/window-to-internet.git](https://github.com/your-username/window-to-internet.git)
    cd window-to-internet
    docker compose up --build -d
    ```
    *(Starts Nginx on Docker port 8000, and FastAPI internally.)*

2.  **Expose to Internet (e.g., Ngrok):**
    ```bash
    ngrok http --domain=<your-domain-name> 8000
    ```
    *(Replace `<your-domain-name>` or omit `--domain` for free tier.)*

Your personal server is now live via the ngrok URL!

## Routes

* **`/`**: Your main personal website.
* **`/notionapp/`**: Example sub-project (FastAPI app, proxied by Nginx).

Serve all your projects under one public domain directly from your laptop.