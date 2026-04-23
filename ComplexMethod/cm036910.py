def test_truncate_prompt_tokens(server: RemoteOpenAIServer, model_name: str):
    long_text = "hello " * 600

    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": long_text, "truncate_prompt_tokens": 5},
    )

    classification_response.raise_for_status()
    output = ClassificationResponse.model_validate(classification_response.json())

    assert len(output.data) == 1
    assert output.data[0].index == 0
    assert hasattr(output.data[0], "probs")
    assert output.usage.prompt_tokens == 5
    assert output.usage.total_tokens == 5

    # invalid_truncate_prompt_tokens
    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": "test", "truncate_prompt_tokens": 513},
    )

    error = classification_response.json()
    assert classification_response.status_code == 400
    assert "truncate_prompt_tokens" in error["error"]["message"]