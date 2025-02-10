import streamlit as st
import openai
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import os
import weaviate.classes as wvc

# API Keys (set these securely in Streamlit secrets)
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
WEAVIATE_URL = st.secrets["WEAVIATE_URL"]
WEAVIATE_API_KEY = st.secrets["WEAVIATE_API_KEY"]

# OpenAI Client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Weaviate Connection
client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),             # Replace with your Weaviate Cloud key
)
collection = client.collections.get("Documents")

# Streamlit UI
st.title("📄 RAG Chatbot")
st.write("Ask questions based on retrieved documents!")

# User Input
user_query = st.text_area("Enter your question:")

# Document Selection
selection_mode = st.radio("Select documents:", ["All Documents", "Choose Documents"])
all_files = {obj["file"] for obj in collection.query.fetch_objects(limit=50).objects}
selected_files = st.multiselect("Select document(s):", list(all_files)) if selection_mode == "Choose Documents" else None

# Retrieve Documents from Weaviate
def retrieve_documents(query, top_k=3, file_names=None):
    results = collection.query.near_text(query, limit=top_k).do()
    if not results["data"]["Get"]["Documents"]:
        return []

    retrieved_texts = []
    for obj in results["data"]["Get"]["Documents"]:
        text = obj["text"]
        page = obj["page"]
        file_ = obj["file"]

        if file_names and file_ not in file_names:
            continue  

        retrieved_texts.append(f"File: {file_}, Page: {page}\nText: {text}")

    return retrieved_texts

# Query OpenAI GPT-3.5
def query_rag(user_query, file_names=None):
    results = retrieve_documents(user_query, top_k=3, file_names=file_names)
    if not results:
        return "No relevant documents found."

    context = "\n\n".join(results)

    prompt = f"""You are an AI assistant answering questions based on retrieved documents. 
    Use the following information to answer the user's question. If the documents don't have the answer, say so.

    ### Retrieved Documents:
    {context}

    ### User Query:
    {user_query}

    ### Answer:
    """

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful chatbot."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# Submit Button
if st.button("Get Answer"):
    if user_query.strip():
        answer = query_rag(user_query, file_names=selected_files)
        st.subheader("Answer:")
        st.write(answer)
    else:
        st.warning("Please enter a question.")
