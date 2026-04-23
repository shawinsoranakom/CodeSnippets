def render_streaming_events(agent, model_choice, temperature, max_turns):
    """Render the streaming events demo"""
    st.header("🌊 Streaming Events Demo")
    st.markdown("Demonstrates advanced streaming event processing and real-time analytics.")

    tab1, tab2 = st.tabs(["Basic Streaming", "Advanced Analytics"])

    with tab1:
        st.subheader("🎯 Basic Streaming with Event Processing")

        with st.form("streaming_basic_form"):
            streaming_input = st.text_area(
                "Your message:", 
                value="Write a comprehensive explanation of how machine learning works, including examples."
            )
            streaming_submitted = st.form_submit_button("Start Streaming")

            if streaming_submitted and streaming_input:
                st.info("🔄 Streaming in progress...")

                # Create containers
                response_container = st.empty()
                stats_container = st.empty()

                try:
                    full_response = ""
                    events_count = 0
                    start_time = time.time()

                    async def process_streaming():
                        nonlocal full_response, events_count

                        async for event in Runner.run_streamed(agent, streaming_input):
                            events_count += 1

                            if hasattr(event, 'content') and event.content:
                                full_response += event.content

                                # Update display
                                response_container.write(f"**Response:**\n{full_response}")

                                # Update stats
                                elapsed = time.time() - start_time
                                char_count = len(full_response)
                                word_count = len(full_response.split())

                                stats_container.metric(
                                    label="Streaming Progress",
                                    value=f"{char_count} chars, {word_count} words",
                                    delta=f"{elapsed:.1f}s elapsed"
                                )

                    asyncio.run(process_streaming())

                    final_time = time.time() - start_time
                    st.success(f"✅ Streaming completed! {events_count} events in {final_time:.2f}s")

                except Exception as e:
                    st.error(f"❌ Streaming error: {e}")

    with tab2:
        st.subheader("📈 Advanced Streaming Analytics")

        with st.form("streaming_analytics_form"):
            analytics_input = st.text_area(
                "Your message:", 
                value="Explain the benefits and challenges of renewable energy in detail."
            )
            analytics_submitted = st.form_submit_button("Stream with Analytics")

            if analytics_submitted and analytics_input:
                st.info("🔄 Streaming with analytics...")

                # Create analytics containers
                response_container = st.empty()
                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)

                try:
                    analytics = {
                        "chunks": [],
                        "chunk_sizes": [],
                        "timestamps": [],
                        "content": ""
                    }

                    start_time = time.time()

                    async def process_analytics_streaming():
                        async for event in Runner.run_streamed(agent, analytics_input):
                            current_time = time.time()

                            if hasattr(event, 'content') and event.content:
                                # Collect analytics
                                analytics["chunks"].append(event.content)
                                analytics["chunk_sizes"].append(len(event.content))
                                analytics["timestamps"].append(current_time - start_time)
                                analytics["content"] += event.content

                                # Update display
                                response_container.write(f"**Response:**\n{analytics['content']}")

                                # Update metrics
                                with metrics_col1:
                                    st.metric("Chunks", len(analytics["chunks"]))

                                with metrics_col2:
                                    avg_chunk_size = sum(analytics["chunk_sizes"]) / len(analytics["chunk_sizes"])
                                    st.metric("Avg Chunk Size", f"{avg_chunk_size:.1f} chars")

                                with metrics_col3:
                                    elapsed = current_time - start_time
                                    if elapsed > 0:
                                        chars_per_sec = len(analytics["content"]) / elapsed
                                        st.metric("Speed", f"{chars_per_sec:.1f} chars/s")

                    asyncio.run(process_analytics_streaming())

                    # Final analytics
                    total_time = time.time() - start_time
                    total_words = len(analytics["content"].split())

                    st.success(f"✅ Analytics complete!")

                    # Display final analytics
                    st.write("**Final Analytics:**")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("Total Time", f"{total_time:.2f}s")

                    with col2:
                        st.metric("Total Words", total_words)

                    with col3:
                        st.metric("Total Chunks", len(analytics["chunks"]))

                    with col4:
                        if total_time > 0:
                            st.metric("Words/Second", f"{total_words/total_time:.1f}")

                except Exception as e:
                    st.error(f"❌ Analytics streaming error: {e}")