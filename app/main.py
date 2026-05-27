from datetime import datetime
import logging
import os
from typing import Optional

from dotenv import load_dotenv
import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Application logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("webvory")

app = FastAPI(
    title="Webvory AI Backend",
    version="0.1.0",
    description="A minimal FastAPI backend with Docker, PostgreSQL, Redis, and NGINX reverse proxy.",
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, socket_timeout=2)

HTML_STYLES = """
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }
  .container {
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 800px;
    padding: 40px;
  }
  .header {
    text-align: center;
    margin-bottom: 30px;
  }
  .header h1 {
    color: #667eea;
    font-size: 2.5em;
    margin-bottom: 10px;
  }
  .header p {
    color: #666;
    font-size: 1.1em;
  }
  .status {
    display: inline-block;
    background: #10b981;
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 0.9em;
    margin-top: 10px;
    font-weight: 600;
  }
  .endpoints {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-top: 30px;
  }
  .endpoint {
    padding: 20px;
    background: #f9fafb;
    border-left: 4px solid #667eea;
    border-radius: 8px;
    transition: all 0.3s ease;
  }
  .endpoint:hover {
    background: #f3f4f6;
    transform: translateX(5px);
  }
  .endpoint h3 {
    color: #667eea;
    margin-bottom: 8px;
    font-size: 1em;
  }
  .endpoint p {
    color: #666;
    font-size: 0.9em;
    line-height: 1.5;
  }
  .endpoint code {
    background: white;
    padding: 4px 8px;
    border-radius: 4px;
    color: #764ba2;
    font-family: 'Courier New', monospace;
    font-size: 0.85em;
  }
  .footer {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #e5e7eb;
    text-align: center;
    color: #999;
    font-size: 0.9em;
  }
  .predict-form {
    margin-top: 30px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
  }
  .form-group {
    margin-bottom: 15px;
  }
  .form-group label {
    display: block;
    color: #333;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .form-group input, .form-group textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 0.95em;
    font-family: inherit;
  }
  .form-group textarea {
    resize: vertical;
    min-height: 80px;
  }
  .form-group input:focus, .form-group textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 30px;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    font-size: 1em;
    transition: all 0.3s ease;
  }
  button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
  }
</style>
"""

@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint with interactive UI."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Webvory AI Backend</title>
        """ + HTML_STYLES + """
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Webvory</h1>
                <p>AI Backend Service</p>
                <span class="status">● Running</span>
            </div>
            
            <div class="endpoints">
                <div class="endpoint">
                    <h3>📊 Health Check</h3>
                    <p><code>GET /health</code></p>
                    <p>Server and Redis status</p>
                </div>
                <div class="endpoint">
                    <h3>✅ Readiness</h3>
                    <p><code>GET /ready</code></p>
                    <p>Service readiness probe</p>
                </div>
            </div>

            <div class="predict-form">
                <h3 style="color: #667eea; margin-bottom: 15px;">🚀 Test Prediction</h3>
                <form id="predictForm">
                    <div class="form-group">
                        <label for="prompt">Prompt</label>
                        <textarea id="prompt" name="prompt" placeholder="Enter your prompt here..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label for="tokens">Max Tokens</label>
                        <input type="number" id="tokens" name="tokens" value="128" min="1" max="1000">
                    </div>
                    <button type="submit">Generate</button>
                </form>
                <div id="result" style="margin-top: 15px; display: none; padding: 15px; background: white; border-radius: 6px;"></div>
            </div>

            <div class="footer">
                <p>Webvory AI Backend • Production Ready • FastAPI + Docker + PostgreSQL + Redis</p>
            </div>
        </div>

        <script>
            document.getElementById('predictForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const prompt = document.getElementById('prompt').value;
                const maxTokens = parseInt(document.getElementById('tokens').value);
                
                try {
                    const response = await fetch('/predict', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({prompt, max_tokens: maxTokens})
                    });
                    
                    const data = await response.json();
                    const resultDiv = document.getElementById('result');
                    
                    if (response.ok) {
                        resultDiv.innerHTML = `
                            <strong>✅ Success</strong><br>
                            <strong>Completion:</strong> <code>${data.completion}</code><br>
                            <strong>Timestamp:</strong> ${data.timestamp}<br>
                            <strong>Model:</strong> ${data.model}
                        `;
                    } else {
                        resultDiv.innerHTML = `<strong>❌ Error:</strong> ${data.detail}`;
                    }
                    resultDiv.style.display = 'block';
                } catch (err) {
                    document.getElementById('result').innerHTML = `<strong>❌ Error:</strong> ${err.message}`;
                    document.getElementById('result').style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    """

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 128

class CompletionResponse(BaseModel):
    prompt: str
    completion: str
    model: str = "mini-ai"
    timestamp: str


@app.get("/health", response_class=HTMLResponse)
def health():
    """Health check endpoint with status page."""
    redis_status = False
    try:
        redis_status = redis_client.ping()
    except redis.RedisError as exc:
        logger.warning("Redis health check failed: %s", exc)

    status = "healthy" if redis_status else "degraded"
    status_color = "#10b981" if redis_status else "#f59e0b"
    redis_badge = "✅ Connected" if redis_status else "⚠️ Disconnected"
    timestamp = datetime.utcnow().isoformat() + "Z"

    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Health Check</title>
        """ + HTML_STYLES + """
    </head>
    <body>
        <div class="container" style="max-width: 500px;">
            <div class="header">
                <h1>📊 Health Status</h1>
                <span class="status" style="background: """ + status_color + """;">● """ + status.upper() + """</span>
            </div>
            
            <div style="margin-top: 30px;">
                <div class="endpoint">
                    <h3>Redis</h3>
                    <p>""" + redis_badge + """</p>
                </div>
                <div class="endpoint" style="margin-top: 15px;">
                    <h3>Timestamp</h3>
                    <p><code>""" + timestamp + """</code></p>
                </div>
            </div>

            <div class="footer">
                <p><a href="/" style="color: #667eea; text-decoration: none;">← Back to Home</a></p>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/ready", response_class=HTMLResponse)
def ready():
    """Readiness endpoint with status page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Readiness Check</title>
        """ + HTML_STYLES + """
    </head>
    <body>
        <div class="container" style="max-width: 500px;">
            <div class="header">
                <h1>✅ Readiness Check</h1>
                <span class="status">● READY</span>
            </div>
            
            <div style="margin-top: 30px;">
                <div class="endpoint">
                    <h3>Service Status</h3>
                    <p>Backend is ready to handle requests</p>
                </div>
            </div>

            <div class="footer">
                <p><a href="/" style="color: #667eea; text-decoration: none;">← Back to Home</a></p>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/predict", response_model=CompletionResponse)
def predict(payload: CompletionRequest):
    """A simple placeholder AI-style completion endpoint."""
    if not payload.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    logger.info("Received prediction request")
    completion = f"Echo: {payload.prompt.strip()}"

    return CompletionResponse(
        prompt=payload.prompt,
        completion=completion,
        timestamp=datetime.utcnow().isoformat() + "Z",
    )
