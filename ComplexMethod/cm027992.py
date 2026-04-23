def main():
    # Custom CSS styling


    st.title("🥸 AI Meme Generator Agent - Browser Use")
    st.info("This AI browser agent does browser automation to generate memes based on your input with browser use. Please enter your API key and describe the meme you want to generate.")

    # Sidebar configuration
    with st.sidebar:
        st.markdown('<p class="sidebar-header">⚙️ Model Configuration</p>', unsafe_allow_html=True)

        # Model selection
        model_choice = st.selectbox(
            "Select AI Model",
            ["Claude", "Deepseek", "OpenAI"],
            index=0,
            help="Choose which LLM to use for meme generation"
        )

        # API key input based on model selection
        api_key = ""
        if model_choice == "Claude":
            api_key = st.text_input("Claude API Key", type="password", 
                                  help="Get your API key from https://console.anthropic.com")
        elif model_choice == "Deepseek":
            api_key = st.text_input("Deepseek API Key", type="password",
                                  help="Get your API key from https://platform.deepseek.com")
        else:
            api_key = st.text_input("OpenAI API Key", type="password",
                                  help="Get your API key from https://platform.openai.com")

    # Main content area
    st.markdown('<p class="header-text">🎨 Describe Your Meme Concept</p>', unsafe_allow_html=True)

    query = st.text_input(
        "Meme Idea Input",
        placeholder="Example: 'Ilya's SSI quietly looking at the OpenAI vs Deepseek debate while diligently working on ASI'",
        label_visibility="collapsed"
    )

    if st.button("Generate Meme 🚀"):
        if not api_key:
            st.warning(f"Please provide the {model_choice} API key")
            st.stop()
        if not query:
            st.warning("Please enter a meme idea")
            st.stop()

        with st.spinner(f"🧠 {model_choice} is generating your meme..."):
            try:
                meme_url = asyncio.run(generate_meme(query, model_choice, api_key))

                if meme_url:
                    st.success("✅ Meme Generated Successfully!")
                    st.image(meme_url, caption="Generated Meme Preview", use_container_width=True)
                    st.markdown(f"""
                        **Direct Link:** [Open in ImgFlip]({meme_url})  
                        **Embed URL:** `{meme_url}`
                    """)
                else:
                    st.error("❌ Failed to generate meme. Please try again with a different prompt.")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("💡 If using OpenAI, ensure your account has GPT-4o access")