async def process_query(
    query: str,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    processor_agent: Agent,
    tts_agent: Agent,
    collection_name: str,
    openai_api_key: str
):
    try:
        query_embedding = list(embedding_model.embed([query]))[0]
        search_response = client.query_points(
            collection_name=collection_name,
            query=query_embedding.tolist(),
            limit=3,
            with_payload=True
        )

        search_results = search_response.points if hasattr(search_response, 'points') else []

        if not search_results:
            raise Exception("No relevant documents found in the vector database")

        context = "Based on the following documentation:\n\n"
        for result in search_results:
            payload = result.payload
            if not payload:
                continue
            url = payload.get('url', 'Unknown URL')
            content = payload.get('content', '')
            context += f"From {url}:\n{content}\n\n"

        context += f"\nUser Question: {query}\n\n"
        context += "Please provide a clear, concise answer that can be easily spoken out loud."

        processor_result = await Runner.run(processor_agent, context)
        processor_response = processor_result.final_output

        tts_result = await Runner.run(tts_agent, processor_response)
        tts_response = tts_result.final_output

        async_openai = AsyncOpenAI(api_key=openai_api_key)
        audio_response = await async_openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=st.session_state.selected_voice,
            input=processor_response,
            instructions=tts_response,
            response_format="mp3"
        )

        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"response_{uuid.uuid4()}.mp3")

        with open(audio_path, "wb") as f:
            f.write(audio_response.content)

        return {
            "status": "success",
            "text_response": processor_response,
            "tts_instructions": tts_response,
            "audio_path": audio_path,
            "sources": [r.payload.get("url", "Unknown URL") for r in search_results if r.payload],
            "query_details": {
                "vector_size": len(query_embedding),
                "results_found": len(search_results),
                "collection_name": collection_name
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }