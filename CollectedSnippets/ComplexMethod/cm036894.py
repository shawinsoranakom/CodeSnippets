async def test_truncate_prompt_tokens(client: openai.AsyncOpenAI, model_name: str):
    input_texts = [
        "Como o Brasil pode fomentar o desenvolvimento de modelos de IA?",
    ]

    # test single embedding
    embedding_response = await client.embeddings.create(
        model=model_name, input=input_texts, extra_body={"truncate_prompt_tokens": 10}
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == 10
    assert embeddings.usage.total_tokens == 10

    input_tokens = [
        1,
        24428,
        289,
        18341,
        26165,
        285,
        19323,
        283,
        289,
        26789,
        3871,
        28728,
        9901,
        340,
        2229,
        385,
        340,
        315,
        28741,
        28804,
        2,
    ]
    embedding_response = await client.embeddings.create(
        model=model_name, input=input_tokens, extra_body={"truncate_prompt_tokens": 10}
    )
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    assert embeddings.usage.prompt_tokens == 10
    assert embeddings.usage.total_tokens == 10

    # invalid_truncate_prompt_tokens
    input_texts = [
        "Como o Brasil pode fomentar o desenvolvimento de modelos de IA?",
    ]

    with pytest.raises(openai.BadRequestError):
        response = await client.embeddings.create(
            model=model_name,
            input=input_texts,
            extra_body={"truncate_prompt_tokens": 8193},
        )
        assert "error" in response.object
        assert (
            "truncate_prompt_tokens value is greater than max_model_len. "
            "Please request a smaller truncation size." in response.message
        )