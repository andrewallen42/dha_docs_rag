# About This App

[Click here](https://dhadocsrag-jz28xl3k2j9lry3keac6jq.streamlit.app) for a simple, proof-of-concept Retrieval-Augmented Generation (RAG) chatbot based on publicly available documents  
published in the [Defense Health Agency Publications Library](https://www.health.mil/Reference-Center/DHA-Publications). The app
is deployed in Streamlit.

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
6. **HRPP Policies and Approvals:** Where should changes to HRPP policies and procedures be submitted for approval?
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
