async def test_completion_request(
    client: openai.AsyncOpenAI, model_name: str, hf_model
):
    # test input: str
    embedding_response = await client.embeddings.create(
        model=model_name,
        input=input_text,
        encoding_format="float",
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == len(input_tokens)
    assert embeddings.usage.total_tokens == len(input_tokens)

    vllm_outputs = [d.embedding for d in embeddings.data]
    run_embedding_correctness_test(hf_model, [input_text], vllm_outputs)

    # test input: list[int]
    embedding_response = await client.embeddings.create(
        model=model_name,
        input=input_tokens,
        encoding_format="float",
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == len(input_tokens)
    assert embeddings.usage.total_tokens == len(input_tokens)

    vllm_outputs = [d.embedding for d in embeddings.data]
    run_embedding_correctness_test(hf_model, [input_text], vllm_outputs)