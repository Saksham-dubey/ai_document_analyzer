from openai import OpenAI
from dotenv import load_dotenv
import os
from workflows.utils.utils import list_pdf_files

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Get PDF Directory
pdf_directory = os.path.join(os.getcwd(), "PDF")
url_list = list_pdf_files(pdf_directory)

# Step 1: Upload PDFs to OpenAI
file_ids = []
for pdf_path in url_list:
    with open(pdf_path, "rb") as file:
        uploaded_file = client.files.create(
            file=file,
            purpose="assistants"
        )
        file_ids.append(uploaded_file.id)

# Step 2: Pass Multiple Files in API Request
content_list = [
    {"type": "input_file", "file_id": file_id} for file_id in file_ids
]  # Dynamically add all file IDs
content_list.append(
    {
        "type": "input_text",
        "text": "Pairwise comparison of plasma samples used where?",
    }
)  # Append the text input

response = client.responses.create(
    model="gpt-4o",
    input=[
        {
            "role": "user",
            "content": content_list
        }
    ]
)

# Step 3: Retrieve Response
response_data = response.output[0].content[0].text
print(response_data)

files = client.files.list()
files = files.data
files_list = []
for file in files:
    files_list.append(file.id)

print(files_list)
for file_id in files_list:
    file = client.files.delete(file_id)
    

