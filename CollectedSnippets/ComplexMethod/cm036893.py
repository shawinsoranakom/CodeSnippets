async def test_completion_request_batched(
    client: openai.AsyncOpenAI, model_name: str, hf_model
):
    N = 10
    input_texts = [input_text] * N

    # test input: list[str]
    embedding_response = await client.embeddings.create(
        model=model_name,
        input=input_texts,
        encoding_format="float",
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == N
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == len(input_tokens) * N
    assert embeddings.usage.total_tokens == len(input_tokens) * N

    vllm_outputs = [d.embedding for d in embeddings.data]
    run_embedding_correctness_test(hf_model, input_texts, vllm_outputs)

    # test list[list[int]]
    embedding_response = await client.embeddings.create(
        model=model_name,
        input=[input_tokens] * N,
        encoding_format="float",
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == N
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == len(input_tokens) * N
    assert embeddings.usage.total_tokens == len(input_tokens) * N

    vllm_outputs = [d.embedding for d in embeddings.data]
    run_embedding_correctness_test(hf_model, input_texts, vllm_outputs)