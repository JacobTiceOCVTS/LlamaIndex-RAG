# LlamaIndex-RAG  
A program utilizing LLM and RAG capabilities to make an AI agent that can answer questions based on user provided PDFs. Uses Gradio and LlamaIndex, running HF embedding model and qwen3 LLM running locally via Ollama.
  
# Files  
**app.py**

This file is the frontend, using gradio to make a simple web page to allow file uploading and user query. It sends user inputs to the backend and displays the AI response

**rag.py**

This is backend file, it powers the logic with LlamaIndex, manages the vector database of user information, and opens the API endpoints
  
# Dependencies  
pypdf

llama-index

fast-api

ollama

shutil

gradio

pip install pypdf llama-index fast-api ollama shutil gradio  
  
# Instructions  
To use simply run the app.py file and use uvicorn to run the rag.py file to handle the FastAPI endpoints
These need to be seperate terminals to function properly
## Example commands:  
**app.py file**

python app.py

**rag.py file**

python -m uvicorn rag:app --host 127.0.0.1 --port 8000

### Once both files are running, the app should work seamlessly  
