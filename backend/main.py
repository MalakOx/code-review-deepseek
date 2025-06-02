from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

app = FastAPI(title="Code Review Assistant", version="1.0.0")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Code Review Assistant API is running"}

@app.post("/review/")
def review_code(code: str = Form(...)):
    if not code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    # Limit code length to prevent timeout
    max_code_length = 5000  # 5000 characters limit
    if len(code) > max_code_length:
        code = code[:max_code_length] + "\n... [Code truncated for analysis]"
    
    # Shorter, more focused prompt to reduce processing time
    prompt = (
        "Review this code briefly for bugs, best practices, and improvements. "
        "Be concise and focus on the most important issues:\n\n"
        f"```\n{code}\n```"
    )
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-coder",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 500,  # Limit response length
                    "num_ctx": 2048     # Limit context window
                }
            },
            timeout=120  # Increased timeout to 2 minutes
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error communicating with Ollama")
        
        result = response.json()
        review_text = result.get("response", "").strip()
        
        if not review_text:
            raise HTTPException(status_code=500, detail="No review generated")
        
        return {"review": review_text, "code_length": len(code)}
    
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Review timed out. Try with smaller code blocks or check if DeepSeek-Coder model is running properly.")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/health")
def health_check():
    try:
        # Test connection to Ollama
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "ollama": "connected"}
        else:
            return {"status": "unhealthy", "ollama": "disconnected"}
    except:
        return {"status": "unhealthy", "ollama": "disconnected"}