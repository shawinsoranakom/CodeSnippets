async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    collection_name: str,
    openai_api_key: str,
    voice: str
) -> Dict:
    """Process user query and generate voice response."""
    try:
        st.info("🔄 Step 1: Generating query embedding and searching documents...")
        # Get query embedding and search
        query_embedding = list(embedding_model.embed([query]))[0]
        st.write(f"Generated embedding of size: {len(query_embedding)}")

        search_response = client.query_points(
            collection_name=collection_name,
            query=query_embedding.tolist(),
            limit=3,
            with_payload=True
        )

        search_results = search_response.points if hasattr(search_response, 'points') else []
        st.write(f"Found {len(search_results)} relevant documents")

        if not search_results:
            raise Exception("No relevant documents found in the vector database")

        st.info("🔄 Step 2: Preparing context from search results...")
        # Prepare context from search results
        context = "Based on the following documentation:\n\n"
        for i, result in enumerate(search_results, 1):
            payload = result.payload
            if not payload:
                continue
            content = payload.get('content', '')
            source = payload.get('file_name', 'Unknown Source')
            context += f"From {source}:\n{content}\n\n"
            st.write(f"Document {i} from: {source}")

        context += f"\nUser Question: {query}\n\n"
        context += "Please provide a clear, concise answer that can be easily spoken out loud."

        st.info("🔄 Step 3: Setting up agents...")
        # Setup agents if not already done
        if not st.session_state.processor_agent or not st.session_state.tts_agent:
            processor_agent, tts_agent = setup_agents(openai_api_key)
            st.session_state.processor_agent = processor_agent
            st.session_state.tts_agent = tts_agent
            st.write("Initialized new processor and TTS agents")
        else:
            st.write("Using existing agents")

        st.info("🔄 Step 4: Generating text response...")
        # Generate text response using processor agent
        processor_result = await Runner.run(st.session_state.processor_agent, context)
        text_response = processor_result.final_output
        st.write(f"Generated text response of length: {len(text_response)}")

        st.info("🔄 Step 5: Generating voice instructions...")
        # Generate voice instructions using TTS agent
        tts_result = await Runner.run(st.session_state.tts_agent, text_response)
        voice_instructions = tts_result.final_output
        st.write(f"Generated voice instructions of length: {len(voice_instructions)}")

        st.info("🔄 Step 6: Generating and playing audio...")
        # Generate and play audio with streaming
        async_openai = AsyncOpenAI(api_key=openai_api_key)

        # First create streaming response
        async with async_openai.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=text_response,
            instructions=voice_instructions,
            response_format="pcm",
        ) as stream_response:
            st.write("Starting audio playback...")
            # Play audio directly using LocalAudioPlayer
            await LocalAudioPlayer().play(stream_response)
            st.write("Audio playback complete")

            st.write("Generating downloadable MP3 version...")
            # Also save as MP3 for download
            audio_response = await async_openai.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=text_response,
                instructions=voice_instructions,
                response_format="mp3"
            )

            temp_dir = tempfile.gettempdir()
            audio_path = os.path.join(temp_dir, f"response_{uuid.uuid4()}.mp3")

            with open(audio_path, "wb") as f:
                f.write(audio_response.content)
            st.write(f"Saved MP3 file to: {audio_path}")

        st.success("✅ Query processing complete!")
        return {
            "status": "success",
            "text_response": text_response,
            "voice_instructions": voice_instructions,
            "audio_path": audio_path,
            "sources": [r.payload.get('file_name', 'Unknown Source') for r in search_results if r.payload]
        }

    except Exception as e:
        st.error(f"❌ Error during query processing: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }