import streamlit as st
import openai
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import os
import weaviate.classes as wvc

def get_question_embedding(question):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    return response.data[0].embedding

def retrieve_documents_from_weviate(user_query, top_k=2):
    query_embedding = get_question_embedding(user_query)
    response = collection.query.near_vector(
        near_vector=query_embedding,
        limit=top_k,
        return_metadata=wvc.query.MetadataQuery(certainty=True),
        distance=0.5
    )
    return response

def query_rag(user_query, top_k=1, file_names=None):
    results = retrieve_documents_from_weviate(user_query, top_k)
    
    if len(results.objects) == 0:
        return "No relevant documents found in this set of DHA documents. Please try a different question."
    
    retrieved_texts = []
    for obj in results.objects:
        text = obj.properties["text"]
        page = obj.properties["page"]
        file_ = obj.properties["file"]
        
        if file_names and file_ not in file_names:
            continue
            
        retrieved_texts.append(f"File: {file_}, Page: {page}, Text: {text}")
        
    if not retrieved_texts:
        files_str = ", ".join(file_names) if file_names else "selected files"
        return f"No relevant documents found in files: {files_str}"
    
    context = "\n\n".join(retrieved_texts)
    files_used = "\n".join([f"File: {obj.properties['file']}, Page: {obj.properties['page']}" for obj in results.objects])
    
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
        messages=[
            {"role": "system", "content": "You are a helpful chatbot."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content, files_used

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
WEAVIATE_URL = st.secrets["WEAVIATE_URL"]
WEAVIATE_API_KEY = st.secrets["WEAVIATE_API_KEY"]

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
)
collection = client.collections.get("Documents")

st.title("📄 RAG Chatbot")

# Tabs
tab1, tab2 = st.tabs(["Chat", "About"])

with tab1:
    st.write("Ask questions based on retrieved documents!")
    user_query = st.text_area("Enter your question:")
    selection_mode = st.radio("Select documents:", ["All Documents", "Choose Documents"])
    all_files = {obj.properties["file"] for obj in collection.query.fetch_objects(limit=50).objects}
    selected_files = st.multiselect("Select document(s):", list(all_files)) if selection_mode == "Choose Documents" else None
    
    if st.button("Get Answer"):
        if user_query.strip():
            answer, files_used_in_answer = query_rag(user_query, file_names=selected_files)
            st.subheader("Answer:")
            st.write(answer)
            st.subheader("Files Used:")
            st.text(files_used_in_answer if files_used_in_answer else "")
        else:
            st.warning("Please enter a question.")

with tab2:
    st.markdown("""
    # About This App
    This is a Retrieval-Augmented Generation (RAG) chatbot powered by OpenAI and Weaviate.
    
    **Features:**
    - Retrieves relevant documents based on user queries.
    - Uses OpenAI's GPT model for answering questions.
    - Allows document selection for more targeted results.
    
    You can edit this section to provide more details about the application!
    """)
