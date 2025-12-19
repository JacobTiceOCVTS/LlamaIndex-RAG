import os
from pypdf import PdfReader
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from fastapi import FastAPI #fastAPI will be used for the main logic
from fastapi.responses import JSONResponse

#initialize agent as none to allow building agent(s) during runtime
agent = None

#initialize API to handle communication between RAG and front-end Gradio
app = FastAPI() #creates an instance of the web appliciation

# dir of documents that will be converted to text
DOCUMENT_DIR_PATH = "./Files/documents"
# dir of the text files that will be interpreted by RAG
TEXT_FILES = "./Files/data/"

os.makedirs(DOCUMENT_DIR_PATH, exist_ok=True)
os.makedirs(TEXT_FILES, exist_ok=True)

# clears directory of text files for clean start
for file in os.listdir(TEXT_FILES):
    os.remove(f"{TEXT_FILES}/{file}")
    print(f"Removed file: {TEXT_FILES}/{file}")
if len(os.listdir(TEXT_FILES)) < 1:
    print("Cleared data to be read")



def convert_documents_to_text(docuements_dir):
    """converts documents in the documents dir to text files and stores them in the data directory"""
    pdfs = os.listdir(docuements_dir)
    i = 0
    # for each pdf in the dir, add each page of text to a string followed by a new line 
    # then delete the original file and store the string as a txt file
    for pdf in pdfs:
        try:
            reader = PdfReader(f"{DOCUMENT_DIR_PATH}/{pdf}")
            text_to_save = ""
            for page in reader.pages:
                text_to_save += page.extract_text() + "\n"
            print(f"Successfully extracted {len(text_to_save)} characters from the text")
            os.remove(f"{docuements_dir}/{pdf}")
            print(f"Removed original file: {pdf}")
        except Exception as e:
            print(f"ERROR: Document could not be interpreted {e}")
            return
        try:
            with open(f"{TEXT_FILES}/{pdf[:-4]}{i}.txt", 'w', encoding='utf-8') as text_file:
                text_file.write(text_to_save)
            print(f"Succesfully saved text to {TEXT_FILES}")
        except Exception as e:
            print(f"ERROR: Failed to save to file. Details: {e}")
        i += 1

# set globals values for the models to use for RAG+LLM
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-base-en-v1.5")
Settings.llm = Ollama(
    model="qwen3:latest",
    request_timeout=360.0,
    # Manually set the context window to limit memory usage
    context_window=8000,
)

def build_agent(noFiles):
    """builds an agent using llamaindex that can access the txt files uploaded, if noFiles is true it will just build a default agent with no dir access"""
    global agent

    # Load data and build index
    if not noFiles:
        documents = SimpleDirectoryReader(TEXT_FILES).load_data()
        index = VectorStoreIndex.from_documents(documents)

        query_engine = index.as_query_engine(
            similarity_top_k=30,
        )

    async def search_documents(query: str) -> str:
        """Use this to search through documents and answer questions based on them"""
        response = await query_engine.aquery(query)
        return str(response)

    agent = AgentWorkflow.from_tools_or_functions(
        [search_documents],
        llm=Settings.llm,
        system_prompt="""You are a knowledgable AI agent that can read documents provided by users and answer questions based on provided information. In the case of multiple documents, use any topical information from any and all files that contain it, be sure to point out connections that may exist. If a user asks about documents, files, or their attributes, give you're best answer based on the contents of the documents. Assume any questions you receive are likely based on the documents uploaded, and answer them based on information from your search_documents function.""",
    )
    print("Successfully Built Agent")


#test endpoint for API
@app.get("/") #makes it so the following function responds when a GET request is sent to the root URL of the http server
def read_root():
    return {"message": "Hello from backend"}

@app.get("/llm")
async def main(user_prompt: str):
    """Uses the agent to generate and return a response based on user query, supplemented by the documents uploaded"""
    global agent
    if agent is None:
        return JSONResponse(status_code=400, content={"error": "No documents indexed. Please upload files first."})
    
    print(f"Prompt received: {user_prompt}")
    try:
        response = await agent.run(user_prompt)
        

        # 'response' is an object, cast to string to get the answer text
        return {"answer": str(response)}

    except Exception as e:
        print(f"SERVER ERROR: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Ollama Connection Failed",
                "detail": f"Could not connect to the AI Model. Error: {e}"
            }
        )

@app.post("/ingest")
async def ingest_endpoint():
    """converts documents and rebuilds agent to ensure new documents are loaded properly"""
    # 1. Convert the uploaded PDFs to text
    convert_documents_to_text(DOCUMENT_DIR_PATH)
    # 2. Rebuild the index and agent
    build_agent(False)
    return {"status": "Done"}

#inital agent is build with noFiles set to true
build_agent(True)