async def make_request_and_correctness_test(dimensions):
        prompts = input_texts * 3

        embedding_response = await client.embeddings.create(
            model=model_info.name,
            input=prompts,
            dimensions=dimensions,
            encoding_format="float",
        )
        embeddings = EmbeddingResponse.model_validate(
            embedding_response.model_dump(mode="json")
        )

        assert embeddings.id is not None
        assert len(embeddings.data) == 3
        assert len(embeddings.data[0].embedding) > 0
        assert embeddings.usage.completion_tokens == 0
        assert embeddings.usage.prompt_tokens > 0
        assert embeddings.usage.total_tokens > 0

        if dimensions is not None:
            assert len(embeddings.data[0].embedding) == dimensions

        vllm_outputs = [d.embedding for d in embeddings.data]
        run_embedding_correctness_test(hf_model, prompts, vllm_outputs, dimensions)