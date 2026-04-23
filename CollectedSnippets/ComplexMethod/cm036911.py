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
    response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "messages": messages},
    )

    response.raise_for_status()
    output = ClassificationResponse.model_validate(response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")
    assert output.usage.prompt_tokens == 51

    # test add_generation_prompt
    response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "messages": messages, "add_generation_prompt": True},
    )

    response.raise_for_status()
    output = ClassificationResponse.model_validate(response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")
    assert output.usage.prompt_tokens == 54

    # test continue_final_message
    response = requests.post(
        server.url_for("classify"),
        json={
            "model": model_name,
            "messages": messages,
            "continue_final_message": True,
        },
    )

    response.raise_for_status()
    output = ClassificationResponse.model_validate(response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")
    assert output.usage.prompt_tokens == 49

    # test add_special_tokens
    # The add_special_tokens parameter doesn't seem to be working with this model.
    response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "messages": messages, "add_special_tokens": True},
    )

    response.raise_for_status()
    output = ClassificationResponse.model_validate(response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")
    assert output.usage.prompt_tokens == 51

    # test continue_final_message with add_generation_prompt
    response = requests.post(
        server.url_for("classify"),
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