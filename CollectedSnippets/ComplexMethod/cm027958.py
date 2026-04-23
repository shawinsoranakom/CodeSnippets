def main() -> None:
    """Main application function."""
    st.set_page_config(
        page_title="Voice RAG Agent",
        page_icon="🎙️",
        layout="wide"
    )

    init_session_state()
    setup_sidebar()

    st.title("🎙️ Voice RAG Agent")
    st.info("Get voice-powered answers to your documentation questions by configuring your API keys and uploading PDF documents. Then, simply ask questions to receive both text and voice responses!")

    # File upload section
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        file_name = uploaded_file.name
        if file_name not in st.session_state.processed_documents:
            with st.spinner('Processing PDF...'):
                try:
                    # Setup Qdrant if not already done
                    if not st.session_state.client:
                        client, embedding_model = setup_qdrant()
                        st.session_state.client = client
                        st.session_state.embedding_model = embedding_model

                    # Process and store document
                    documents = process_pdf(uploaded_file)
                    if documents:
                        store_embeddings(
                            st.session_state.client,
                            st.session_state.embedding_model,
                            documents,
                            COLLECTION_NAME
                        )
                        st.session_state.processed_documents.append(file_name)
                        st.success(f"✅ Added PDF: {file_name}")
                        st.session_state.setup_complete = True
                except Exception as e:
                    st.error(f"Error processing document: {str(e)}")

    # Display processed documents
    if st.session_state.processed_documents:
        st.sidebar.header("📚 Processed Documents")
        for doc in st.session_state.processed_documents:
            st.sidebar.text(f"📄 {doc}")

    # Query interface
    query = st.text_input(
        "What would you like to know about the documentation?",
        placeholder="e.g., How do I authenticate API requests?",
        disabled=not st.session_state.setup_complete
    )

    if query and st.session_state.setup_complete:
        with st.status("Processing your query...", expanded=True) as status:
            try:
                result = asyncio.run(process_query(
                    query,
                    st.session_state.client,
                    st.session_state.embedding_model,
                    COLLECTION_NAME,
                    st.session_state.openai_api_key,
                    st.session_state.selected_voice
                ))

                if result["status"] == "success":
                    status.update(label="✅ Query processed!", state="complete")

                    st.markdown("### Response:")
                    st.write(result["text_response"])

                    if "audio_path" in result:
                        st.markdown(f"### 🔊 Audio Response (Voice: {st.session_state.selected_voice})")
                        st.audio(result["audio_path"], format="audio/mp3", start_time=0)

                        with open(result["audio_path"], "rb") as audio_file:
                            audio_bytes = audio_file.read()
                            st.download_button(
                                label="📥 Download Audio Response",
                                data=audio_bytes,
                                file_name=f"voice_response_{st.session_state.selected_voice}.mp3",
                                mime="audio/mp3"
                            )

                    st.markdown("### Sources:")
                    for source in result["sources"]:
                        st.markdown(f"- {source}")
                else:
                    status.update(label="❌ Error processing query", state="error")
                    st.error(f"Error: {result.get('error', 'Unknown error occurred')}")

            except Exception as e:
                status.update(label="❌ Error processing query", state="error")
                st.error(f"Error processing query: {str(e)}")

    elif not st.session_state.setup_complete:
        st.info("👈 Please configure the system and upload documents first!")