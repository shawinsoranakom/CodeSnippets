async def test_matryoshka(
    model_info: EmbedModelInfo, server: RemoteOpenAIServer, hf_model: HfRunner
):
    client = server.get_async_client()

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

    if model_info.is_matryoshka:
        valid_dimensions: list[int | None] = [None]
        if model_info.matryoshka_dimensions is not None:
            valid_dimensions += model_info.matryoshka_dimensions[:2]

        for dimensions in valid_dimensions:
            await make_request_and_correctness_test(dimensions)

        invalid_dimensions: list[int | None] = [-1]
        if model_info.matryoshka_dimensions is not None:
            assert 5 not in model_info.matryoshka_dimensions
            invalid_dimensions.append(5)

        for dimensions in invalid_dimensions:
            with pytest.raises(openai.BadRequestError):
                await make_request_and_correctness_test(dimensions)

    else:
        for dimensions in [None]:
            await make_request_and_correctness_test(dimensions)

        for dimensions in [-1, 16]:
            with pytest.raises(openai.BadRequestError):
                await make_request_and_correctness_test(dimensions)