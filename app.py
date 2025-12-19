import shutil
import gradio as gr #used for frontend, launches a very easy to use web server
import requests #used for the api calls

FASTAPI_URL = "http://127.0.0.1:8000/llm" #url endpoint for the llm

def process_files(file_list):
    if file_list is None:
        return ("No Files Uploaded")
    
    num_files = len(file_list)

    saved_count = 0
    save_results = []

    for file in file_list:
        try:
            destination_path = f"./Files/documents/"
            original_name = file.name[77:-4]
            file_name = f"{original_name} ({saved_count}).pdf"
            temp_file_to_be_copied = file.name

            shutil.copyfile(temp_file_to_be_copied, (destination_path+file_name))

            saved_count += 1
            save_results.append(f"File: {file_name} successfully saved to {destination_path}")
        except Exception as e:
            save_results.append(f"Error saving {file_name}: {e}")

    try:
        requests.post("http://127.0.0.1:8000/ingest")
        save_results.append("Backend successfully triggered to ingest files.")
    except Exception as e:
        save_results.append(f"Error triggering backend: {e}")
    
    save_results_formatted = "\n".join(save_results)
    return (f"Saved {saved_count} files out of {num_files}\nResults: \n{save_results_formatted}")



#function sends the query to the fastapi backend and returns response or error
def query_backend(user_input):
    #status message announcing what the program is doing
    print(f"Recieved input: {user_input}. Sending request to FastAPI...")

    #trys getting the api response, turning it into json, then returning the answer
    try:
        response = requests.get(FASTAPI_URL, params={"user_prompt":user_input})

        response.raise_for_status()

        data = response.json()
        return data.get("answer", "Error: 'answer' key not found in response")
    
    #returns error if this process fails at any point
    except Exception as e:
        return f"ERROR: Could not get response from FastAPI. Details: {e}"



with gr.Blocks(title="PDF Summarizing") as interface:
    gr.Markdown("# Project 1: Full-Stack Gradio Frontend Test")
    gr.Markdown("Interface running on port 7860, FastAPI on port 8000")
    
    # Query section
    with gr.Row():
        text_inputs = gr.Textbox(lines=10, placeholder="Type your question here...", label="Query")
        text_outputs = gr.Textbox(lines=10, label="Response")
    
    submit_query = gr.Button("Submit Query")
    submit_query.click(
        fn=query_backend,
        inputs=text_inputs,
        outputs=text_outputs,
    )
    
    # File upload section
    gr.Markdown("## PDF Uploader")
    with gr.Row():
        file_outputs = gr.Textbox(lines=4, label="File status")

    pdfUploader = gr.File(
        file_count="multiple",
        file_types=[".pdf"],
        label="Upload pdf files for LLM to read"
    )
    
    upload = gr.Button("Upload Files")
    upload.click(
        fn=process_files,
        inputs=pdfUploader,
        outputs=file_outputs,
    )

#runs the interface on a different port than the backend
interface.launch(server_name="0.0.0.0", server_port=7862)