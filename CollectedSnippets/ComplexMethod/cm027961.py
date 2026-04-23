def run_streamlit():
    st.set_page_config(
        page_title="Customer Support Voice Agent",
        page_icon="🎙️",
        layout="wide"
    )

    init_session_state()
    sidebar_config()

    st.title("🎙️ Customer Support Voice Agent")
    st.markdown("""
    Get OpenAI SDK voice-powered answers to your documentation questions! Simply:
    1. Configure your API keys in the sidebar
    2. Enter the documentation URL you want to learn about or have questions about
    3. Ask your question below and get both text and voice responses
    """)

    query = st.text_input(
        "What would you like to know about the documentation?",
        placeholder="e.g., How do I authenticate API requests?",
        disabled=not st.session_state.setup_complete
    )

    if query and st.session_state.setup_complete:
        with st.status("Processing your query...", expanded=True) as status:
            try:
                st.markdown("🔄 Searching documentation and generating response...")
                result = asyncio.run(process_query(
                    query,
                    st.session_state.client,
                    st.session_state.embedding_model,
                    st.session_state.processor_agent,
                    st.session_state.tts_agent,
                    "docs_embeddings",
                    st.session_state.openai_api_key
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
        st.info("👈 Please configure the system using the sidebar first!")