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
        return "No relevant documents found in this set of DHA documents. Please try a different question.", None
    
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
        return f"No relevant documents found in files: {files_str}", None
    
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

st.title("📄 DHA Publications RAG Chatbot")

# Tabs
tab1, tab2 = st.tabs(["Chat", "About"])

with tab1:
    st.write("Ask questions about DHA publications!")
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

This is a simple, proof-of-concept Retrieval-Augmented Generation (RAG) chatbot based on publicly available documents  
published in the [Defense Health Agency Publications Library](https://www.health.mil/Reference-Center/DHA-Publications).

## Get Started

Given the technical nature of the documents, it might be challenging to think of a relevant query to test the chatbot's capabilities.  
You can test the RAG chatbot by:

### 1. Using one of the following queries and choosing **"All Documents"**:

#### Example Queries:
1. **Gift Offers:** What are the key components that a proffer needs to include when submitting a gift offer to DHA according to DHA-AI 7000.01?
2. **Trainee Grievances:** What are the requirements and procedures for addressing trainee grievances in the context of DHA-PI 6015.24 and ACGME requirements?
3. **Legal Matters:** Which legal matters arising from or relating to the Defense Health Network (DHN) and Military Treatment Facility (MTF) operations should be referred to designated DHA OGC legal personnel, and where can a roster of these legal professionals be found for alignment with DHNs and MTFs?
4. **Physician Training Programs:** What is the definition of "Complement" in the context of physician training programs according to the DHA-PI 6015.24 document excerpt?
5. **GME Program Directors:** Retrieve a list of GME program directors responsible for overseeing the development and conduct of GME programs in accordance with ACGME policies and institutional GME policies.
6. **Abbreviations & Acronyms:** What are the abbreviations and acronyms defined in DHA-AI 6025.12?
7. **Waivers:** What is the process for requesting a waiver related to compliance with DHA-IPM 24-004, and who has the authority to grant such waivers within the organization?
8. **Minor Notification Guidelines:** Retrieve guidelines on when healthcare providers should notify a minor's parent, legal guardian, or surrogate decision maker based on complicating circumstances such as life-threatening conditions or behavior changes affecting healthcare maturity.
9. **Outpatient Prescription Dispensing:** What are the standardized procedures for outpatient prescription dispensing at MTF pharmacies according to DHA-AI 6025.30?
10. **Newborn Safety:** Retrieve information on the Association of Women’s Health, Obstetric, and Neonatal Nurses (AWHONN) Practice Brief Number 9 regarding the prevention of newborn falls/drops in hospitals.

### 2. Asking about something **decidedly NOT** relevant to DHA published documents, such as:
   - What is the state bird of Wyoming?

---

## Features:
- Based on ~25 documents from 2024
- Retrieves pertinent documents and answers user queries, if relevant to content in one or more of the 25 DHA documents.
- Allows document selection for more targeted results.
- Uses OpenAI embeddings and **GPT-3.5 Turbo** for generation.  
  Vectors are stored in Weaviate cloud vector storage.

## Caveats:
- This proof-of-concept was created quickly. Documents were chunked/vectorized at the page level rather than hierarchically.
""")

