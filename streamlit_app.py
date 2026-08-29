import io
import requests
import streamlit as st

API_URL = st.sidebar.text_input("API base URL", value="http://localhost:8000")

st.title("Enterprise Financial Document Intelligence — Demo UI")

st.markdown("Upload documents, index them, and ask questions over your corpus.")

with st.expander("Upload Document"):
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "md", "pdf"])
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        resp = requests.post(f"{API_URL}/upload", files=files)
        if resp.ok:
            st.success("Uploaded")
            st.json(resp.json())
        else:
            st.error(f"Upload failed: {resp.status_code}")

with st.expander("Index Documents"):
    if st.button("Run index"):
        resp = requests.post(f"{API_URL}/index")
        if resp.ok:
            st.success("Indexing finished")
            st.json(resp.json())
        else:
            st.error(f"Index failed: {resp.status_code} - {resp.text}")

st.markdown("---")

st.subheader("Query the corpus")
q = st.text_input("Enter your question")
top_k = st.number_input("Top K", value=5, min_value=1, max_value=50)
if st.button("Ask"):
    if not q:
        st.warning("Type a question first")
    else:
        payload = {"query": q, "top_k": int(top_k)}
        try:
            resp = requests.post(f"{API_URL}/query", json=payload, timeout=60)
            if resp.ok:
                data = resp.json()
                st.subheader("Answer")
                st.write(data.get("answer"))
                st.subheader("Candidates")
                for c in data.get("candidates", []):
                    st.markdown(f"**id:** {c.get('id')}  ")
                    st.write(c.get("text"))
                    st.write(c.get("metadata"))
            else:
                st.error(f"Query failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            st.error(f"Error calling API: {e}")
