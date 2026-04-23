async def test_chat_request(
    server: RemoteOpenAIServer, client: openai.AsyncOpenAI, model_name: str
):
    messages = [
        {
            "role": "user",
            "content": "The cat sat on the mat.",
        },
        {
            "role": "assistant",
            "content": "A feline was resting on a rug.",
        },
        {
            "role": "user",
            "content": "Stars twinkle brightly in the night sky.",
        },
    ]

    # test chat request basic usage
    chat_response = requests.post(
        server.url_for("v1/embeddings"),
        json={
            "model": model_name,
            "messages": messages,
            "encoding_format": "float",
        },
    )
    chat_response.raise_for_status()
    chat_embeddings = EmbeddingResponse.model_validate(chat_response.json())

    tokenizer = get_tokenizer(tokenizer_name=model_name)
    prompt = tokenizer.apply_chat_template(
        messages,
        chat_template=DUMMY_CHAT_TEMPLATE,
        add_generation_prompt=True,
        continue_final_message=False,
        tokenize=False,
    )
    completion_response = await client.embeddings.create(
        model=model_name,
        input=prompt,
        encoding_format="float",
        # To be consistent with chat
        extra_body={"add_special_tokens": False},
    )
    completion_embeddings = EmbeddingResponse.model_validate(
        completion_response.model_dump(mode="json")
    )

    assert chat_embeddings.id is not None
    assert completion_embeddings.id is not None
    assert chat_embeddings.created <= completion_embeddings.created
    # Use tolerance-based comparison for embeddings
    check_embeddings_close(
        embeddings_0_lst=[d.embedding for d in chat_embeddings.data],
        embeddings_1_lst=[d.embedding for d in completion_embeddings.data],
        name_0="chat",
        name_1="completion",
    )
    assert chat_embeddings.model_dump(exclude={"id", "created", "data"}) == (
        completion_embeddings.model_dump(exclude={"id", "created", "data"})
    )

    # test add_generation_prompt
    response = requests.post(
        server.url_for("v1/embeddings"),
        json={"model": model_name, "messages": messages, "add_generation_prompt": True},
    )

    response.raise_for_status()
    output = EmbeddingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 34

    # test continue_final_message
    response = requests.post(
        server.url_for("v1/embeddings"),
        json={
            "model": model_name,
            "messages": messages,
            "continue_final_message": True,
        },
    )

    response.raise_for_status()
    output = EmbeddingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 33

    # test add_special_tokens
    response = requests.post(
        server.url_for("v1/embeddings"),
        json={"model": model_name, "messages": messages, "add_special_tokens": True},
    )

    response.raise_for_status()
    output = EmbeddingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 36

    # test continue_final_message with add_generation_prompt
    response = requests.post(
        server.url_for("v1/embeddings"),
        json={
            "model": model_name,
            "messages": messages,
            "continue_final_message": True,
            "add_generation_prompt": True,
        },
    )
    assert (
        "Cannot set both `continue_final_message` and `add_generation_prompt` to True."
        in response.json()["error"]["message"]
    )