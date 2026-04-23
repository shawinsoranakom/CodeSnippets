async def test_chat_request(server: RemoteOpenAIServer, model_name: str):
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
        server.url_for("pooling"),
        json={
            "model": model_name,
            "messages": messages,
            "encoding_format": "float",
        },
    )
    chat_response.raise_for_status()
    chat_poolings = PoolingResponse.model_validate(chat_response.json())

    tokenizer = get_tokenizer(tokenizer_name=model_name, trust_remote_code=True)
    prompt = tokenizer.apply_chat_template(
        messages,
        chat_template=DUMMY_CHAT_TEMPLATE,
        add_generation_prompt=True,
        continue_final_message=False,
        tokenize=False,
    )
    completions_response = requests.post(
        server.url_for("pooling"),
        json={
            "model": model_name,
            "input": prompt,
            "encoding_format": "float",
            # To be consistent with chat
            "add_special_tokens": False,
        },
    )
    completions_response.raise_for_status()
    completion_poolings = PoolingResponse.model_validate(completions_response.json())

    assert chat_poolings.id is not None
    assert completion_poolings.id is not None
    assert chat_poolings.created <= completion_poolings.created
    assert chat_poolings.model_dump(exclude={"id", "created"}) == (
        completion_poolings.model_dump(exclude={"id", "created"})
    )

    # test add_generation_prompt
    response = requests.post(
        server.url_for("pooling"),
        json={"model": model_name, "messages": messages, "add_generation_prompt": True},
    )

    response.raise_for_status()
    output = PoolingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 33

    # test continue_final_message
    # The continue_final_message parameter doesn't seem to be working with this model.
    response = requests.post(
        server.url_for("pooling"),
        json={
            "model": model_name,
            "messages": messages,
            "continue_final_message": True,
        },
    )

    response.raise_for_status()
    output = PoolingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 33

    # test add_special_tokens
    response = requests.post(
        server.url_for("pooling"),
        json={"model": model_name, "messages": messages, "add_special_tokens": True},
    )

    response.raise_for_status()
    output = PoolingResponse.model_validate(response.json())

    assert output.object == "list"
    assert len(output.data) == 1
    assert output.model == MODEL_NAME
    assert output.usage.prompt_tokens == 34

    # test continue_final_message with add_generation_prompt
    response = requests.post(
        server.url_for("pooling"),
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