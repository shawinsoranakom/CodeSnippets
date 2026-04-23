def main() -> None:
    st.title("O3-Mini Coding Agent")

    # Add timeout info in sidebar
    initialize_session_state()
    setup_sidebar()
    with st.sidebar:
        st.info("⏱️ Code execution timeout: 30 seconds")

    # Check all required API keys
    if not (st.session_state.openai_key and 
            st.session_state.gemini_key and 
            st.session_state.e2b_key):
        st.warning("Please enter all required API keys in the sidebar.")
        return

    vision_agent, coding_agent, execution_agent = create_agents()

    # Clean, single-column layout
    uploaded_image = st.file_uploader(
        "Upload an image of your coding problem (optional)",
        type=['png', 'jpg', 'jpeg']
    )

    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

    user_query = st.text_area(
        "Or type your coding problem here:",
        placeholder="Example: Write a function to find the sum of two numbers. Include sample input/output cases.",
        height=100
    )

    # Process button
    if st.button("Generate & Execute Solution", type="primary"):
        if uploaded_image and not user_query:
            # Process image with Gemini
            with st.spinner("Processing image..."):
                try:
                    # Save uploaded file to temporary location
                    image = Image.open(uploaded_image)
                    extracted_query = process_image_with_gemini(vision_agent, image)

                    if extracted_query.startswith("Failed to process"):
                        st.error(extracted_query)
                        return

                    st.info("📝 Extracted Problem:")
                    st.write(extracted_query)

                    # Pass extracted query to coding agent
                    with st.spinner("Generating solution..."):
                        response: RunOutput = coding_agent.run(extracted_query)
                except Exception as e:
                    st.error(f"Error processing image: {str(e)}")
                    return

        elif user_query and not uploaded_image:
            # Direct text input processing
            with st.spinner("Generating solution..."):
                response: RunOutput = coding_agent.run(user_query)

        elif user_query and uploaded_image:
            st.error("Please use either image upload OR text input, not both.")
            return
        else:
            st.warning("Please provide either an image or text description of your coding problem.")
            return

        # Display and execute solution
        if 'response' in locals():
            st.divider()
            st.subheader("💻 Solution")

            # Extract code from markdown response
            code_blocks = response.content.split("```python")
            if len(code_blocks) > 1:
                code = code_blocks[1].split("```")[0].strip()

                # Display the code
                st.code(code, language="python")

                # Execute code with execution agent
                with st.spinner("Executing code..."):
                    # Always initialize a fresh sandbox for each execution
                    initialize_sandbox()

                    if st.session_state.sandbox:
                        execution_results = execute_code_with_agent(
                            execution_agent,
                            code,
                            st.session_state.sandbox
                        )

                        # Display execution results
                        st.divider()
                        st.subheader("🚀 Execution Results")
                        st.markdown(execution_results)

                        # Try to display files if available
                        try:
                            files = st.session_state.sandbox.files.list("/")
                            if files:
                                st.markdown("📁 **Generated Files:**")
                                st.json(files)
                        except:
                            pass