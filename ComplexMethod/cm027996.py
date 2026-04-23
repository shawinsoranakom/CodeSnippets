def main():
    st.set_page_config(page_title="LLM-Powered Hybrid Search-RAG Assistant", layout="wide")

    for state_var in ['chat_history', 'documents_loaded', 'my_config', 'user_env']:
        if state_var not in st.session_state:
            st.session_state[state_var] = [] if state_var == 'chat_history' else False if state_var == 'documents_loaded' else None if state_var == 'my_config' else {}

    with st.sidebar:
        st.title("Configuration")
        openai_key = st.text_input("OpenAI API Key", value=st.session_state.get('openai_key', ''), type="password", placeholder="sk-...")
        anthropic_key = st.text_input("Anthropic API Key", value=st.session_state.get('anthropic_key', ''), type="password", placeholder="sk-ant-...")
        cohere_key = st.text_input("Cohere API Key", value=st.session_state.get('cohere_key', ''), type="password", placeholder="Enter Cohere key")
        db_url = st.text_input("Database URL", value=st.session_state.get('db_url', 'sqlite:///raglite.sqlite'), placeholder="sqlite:///raglite.sqlite")

        if st.button("Save Configuration"):
            try:
                if not all([openai_key, anthropic_key, cohere_key, db_url]):
                    st.error("All fields are required!")
                    return

                for key, value in {'openai_key': openai_key, 'anthropic_key': anthropic_key, 'cohere_key': cohere_key, 'db_url': db_url}.items():
                    st.session_state[key] = value

                st.session_state.my_config = initialize_config(openai_key=openai_key, anthropic_key=anthropic_key, cohere_key=cohere_key, db_url=db_url)
                st.session_state.user_env = {"ANTHROPIC_API_KEY": anthropic_key}
                st.success("Configuration saved successfully!")
            except Exception as e:
                st.error(f"Configuration error: {str(e)}")

    st.title("👀 RAG App with Hybrid Search")

    if st.session_state.my_config:
        uploaded_files = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True, key="pdf_uploader")

        if uploaded_files:
            success = False
            for uploaded_file in uploaded_files:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    if process_document(temp_path):
                        st.success(f"Successfully processed: {uploaded_file.name}")
                        success = True
                    else:
                        st.error(f"Failed to process: {uploaded_file.name}")
                    os.remove(temp_path)

            if success:
                st.session_state.documents_loaded = True
                st.success("Documents are ready! You can now ask questions about them.")

    if st.session_state.documents_loaded:
        for msg in st.session_state.chat_history:
            with st.chat_message("user"): st.write(msg[0])
            with st.chat_message("assistant"): st.write(msg[1])

        user_input = st.chat_input("Ask a question about the documents...")
        if user_input:
            with st.chat_message("user"): st.write(user_input)
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                try:
                    reranked_chunks = perform_search(query=user_input)
                    if not reranked_chunks or len(reranked_chunks) == 0:
                        logger.info("No relevant documents found. Falling back to Claude.")
                        st.info("No relevant documents found. Using general knowledge to answer.")
                        full_response = handle_fallback(user_input)
                    else:
                        formatted_messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": msg}
                                           for i, msg in enumerate([m for pair in st.session_state.chat_history for m in pair]) if msg]

                        response_stream = rag(prompt=user_input, 
                                           system_prompt=RAG_SYSTEM_PROMPT,
                                           search=hybrid_search, 
                                           messages=formatted_messages,
                                           max_contexts=5, 
                                           config=st.session_state.my_config)

                        full_response = ""
                        for chunk in response_stream:
                            full_response += chunk
                            message_placeholder.markdown(full_response + "▌")

                    message_placeholder.markdown(full_response)
                    st.session_state.chat_history.append((user_input, full_response))
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        st.info("Please configure your API keys and upload documents to get started." if not st.session_state.my_config else "Please upload some documents to get started.")