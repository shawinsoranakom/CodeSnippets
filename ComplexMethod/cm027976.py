def render_execution_methods(agent, model_choice, temperature, max_turns):
    """Render the execution methods demo"""
    st.header("⚡ Execution Methods Demo")
    st.markdown("Compare synchronous, asynchronous, and streaming execution patterns.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🔄 Synchronous (Blocking)")
        st.caption("Runner.run_sync() - Blocks until complete")

        with st.form("sync_form"):
            sync_input = st.text_area("Your message:", key="sync_input", value="Explain synchronous execution in simple terms")
            sync_submitted = st.form_submit_button("Run Sync")

            if sync_submitted and sync_input:
                with st.spinner("Processing synchronously..."):
                    start_time = time.time()

                    try:
                        result = Runner.run_sync(agent, sync_input)
                        execution_time = time.time() - start_time

                        st.success(f"✅ Completed in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)

                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    with col2:
        st.subheader("⚡ Asynchronous (Non-blocking)")
        st.caption("Runner.run() - Returns awaitable")

        with st.form("async_form"):
            async_input = st.text_area("Your message:", key="async_input", value="Explain asynchronous execution benefits")
            async_submitted = st.form_submit_button("Run Async")

            if async_submitted and async_input:
                with st.spinner("Processing asynchronously..."):
                    start_time = time.time()

                    try:
                        result = asyncio.run(Runner.run(agent, async_input))
                        execution_time = time.time() - start_time

                        st.success(f"✅ Completed in {execution_time:.2f}s")
                        st.write("**Response:**")
                        st.write(result.final_output)

                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    with col3:
        st.subheader("🌊 Streaming (Real-time)")
        st.caption("Runner.run_streamed() - Live updates")

        with st.form("streaming_form"):
            streaming_input = st.text_area("Your message:", key="streaming_input", value="Write a detailed explanation of streaming execution")
            streaming_submitted = st.form_submit_button("Run Streaming")

            if streaming_submitted and streaming_input:
                st.info("🔄 Streaming response...")

                # Create containers for streaming output
                response_container = st.empty()
                progress_container = st.empty()

                try:
                    full_response = ""
                    start_time = time.time()

                    async def stream_response():
                        nonlocal full_response
                        async for event in Runner.run_streamed(agent, streaming_input):
                            if hasattr(event, 'content') and event.content:
                                full_response += event.content
                                response_container.write(f"**Response:**\n{full_response}")

                        execution_time = time.time() - start_time
                        progress_container.success(f"✅ Streaming completed in {execution_time:.2f}s")

                    asyncio.run(stream_response())

                except Exception as e:
                    st.error(f"❌ Streaming error: {e}")