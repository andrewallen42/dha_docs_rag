import os
import re
import json
import fitz  # PyMuPDF
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import weaviate.classes as wvc
from openai import OpenAI

# Specify the folder path for PDFs (Update this to your actual path)
FOLDER_PATH = "path to pdfs here"

# Retrieve all PDF file paths in the specified folder
file_paths = [
    os.path.join(FOLDER_PATH, filename)
    for filename in os.listdir(FOLDER_PATH)
    if filename.lower().endswith('.pdf')
]

# Sort files to ensure consistent processing order
file_paths.sort()

# Initialize lists to store extracted text and glossary data
results = []
glossary_dict = {}

def extract_abbreviations(text):
    """Extracts abbreviations and their definitions from text."""
    lines = text.split("\n")
    abbrev_dict = {}
    for i in range(len(lines) - 1):
        if lines[i].strip() and lines[i + 1].strip():
            abbrev_dict[lines[i].strip()] = lines[i + 1].strip()
    return abbrev_dict

# Process each PDF file to extract text and detect glossaries
for file_path in file_paths:
    doc = fitz.open(file_path)
    glossary_found = False

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()

        # Store page content
        results.append({
            "file": os.path.basename(file_path),
            "page": page_num + 1,
            "category": "PAGE_CONTENT",
            "text": text
        })

        # Detect and extract glossary terms (if found near the end of the document)
        if "GLOSSARY" in text and page_num >= len(doc) - 10:
            glossary_found = True
            glossary_dict.update(extract_abbreviations(text))
            results.append({
                "file": os.path.basename(file_path),
                "page": page_num + 1,
                "category": "GLOSSARY",
                "text": text
            })

# Replace glossary abbreviations in the extracted text with their definitions
if glossary_dict:
    for i in range(len(results)):
        text = results[i]["text"]
        for acronym, definition in glossary_dict.items():
            text = re.sub(rf'\b{acronym}\b', f'{acronym} ({definition})', text)
        results[i]["text"] = text

def list_to_string(lst):
    """Converts a list to a hyphen-separated string."""
    return '-'.join(map(str, lst))

# Convert list-based page numbers to string format
for r in results:
    if isinstance(r['page'], list):
        r['page'] = list_to_string(r['page'])

# Load API keys from environment variables for security
WCD_URL = os.getenv("WEAVIATE_URL")  # Weaviate cloud URL
WCD_API_KEY = os.getenv("WEAVIATE_API_KEY")  # Weaviate API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API key

# Initialize OpenAI client for generating text embeddings
oai_client = OpenAI(api_key=OPENAI_API_KEY)

# Generate vector embeddings for each extracted text segment
for item in results:
    response = oai_client.embeddings.create(
        model="text-embedding-3-small",
        input=item["text"]
    )
    item["vector"] = response.data[0].embedding

# Connect to Weaviate Cloud instance
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WCD_URL,
    auth_credentials=Auth.api_key(WCD_API_KEY),
)

# Ensure the Weaviate connection is successful
if not client.is_ready():
    raise Exception("Weaviate connection failed.")

# Retrieve or create the "Documents" collection in Weaviate
if "Documents" not in client.collections.list():
    documents = client.collections.create(
        "Documents",
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
    )
else:
    documents = client.collections.get("Documents")

# Prepare extracted data for insertion into Weaviate
doc_objs = [
    wvc.data.DataObject(
        properties={
            "file": str(d["file"]),
            "page": str(d["page"]),
            "text": str(d["text"]),
        },
        vector=d["vector"]
    )
    for d in results
]

# Insert the processed documents into Weaviate
documents.data.insert_many(doc_objs)

print("Document processing and insertion completed successfully.")
