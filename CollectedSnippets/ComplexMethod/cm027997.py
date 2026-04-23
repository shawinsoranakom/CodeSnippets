def main():
    st.set_page_config(page_title="RAG-as-a-Service", layout="wide")
    initialize_session_state()

    st.title(":linked_paperclips: RAG-as-a-Service")

    # API Keys Section
    with st.expander("🔑 API Keys Configuration", expanded=not st.session_state.api_keys_submitted):
        col1, col2 = st.columns(2)
        with col1:
            ragie_key = st.text_input("Ragie API Key", type="password", key="ragie_key")
        with col2:
            anthropic_key = st.text_input("Anthropic API Key", type="password", key="anthropic_key")

        if st.button("Submit API Keys"):
            if ragie_key and anthropic_key:
                try:
                    st.session_state.pipeline = RAGPipeline(ragie_key, anthropic_key)
                    st.session_state.api_keys_submitted = True
                    st.success("API keys configured successfully!")
                except Exception as e:
                    st.error(f"Error configuring API keys: {str(e)}")
            else:
                st.error("Please provide both API keys.")

    # Document Upload Section
    if st.session_state.api_keys_submitted:
        st.markdown("### 📄 Document Upload")
        doc_url = st.text_input("Enter document URL")
        doc_name = st.text_input("Document name (optional)")

        col1, col2 = st.columns([1, 3])
        with col1:
            upload_mode = st.selectbox("Upload mode", ["fast", "accurate"])

        if st.button("Upload Document"):
            if doc_url:
                try:
                    with st.spinner("Uploading document..."):
                        st.session_state.pipeline.upload_document(
                            url=doc_url,
                            name=doc_name if doc_name else None,
                            mode=upload_mode
                        )
                        time.sleep(5)  # Wait for indexing
                        st.session_state.document_uploaded = True
                        st.success("Document uploaded and indexed successfully!")
                except Exception as e:
                    st.error(f"Error uploading document: {str(e)}")
            else:
                st.error("Please provide a document URL.")

    # Query Section
    if st.session_state.document_uploaded:
        st.markdown("### 🔍 Query Document")
        query = st.text_input("Enter your query")

        if st.button("Generate Response"):
            if query:
                try:
                    with st.spinner("Generating response..."):
                        response = st.session_state.pipeline.process_query(query)
                        st.markdown("### Response:")
                        st.markdown(response)
                except Exception as e:
                    st.error(f"Error generating response: {str(e)}")
            else:
                st.error("Please enter a query.")