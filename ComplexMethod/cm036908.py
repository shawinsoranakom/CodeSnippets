def test_completion_request(server: RemoteOpenAIServer, model_name: str):
    # test input: str
    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": input_text},
    )

    classification_response.raise_for_status()
    output = ClassificationResponse.model_validate(classification_response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")

    # test input: list[int]
    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": input_tokens},
    )

    classification_response.raise_for_status()
    output = ClassificationResponse.model_validate(classification_response.json())

    assert output.object == "list"
    assert output.model == MODEL_NAME
    assert len(output.data) == 1
    assert hasattr(output.data[0], "label")
    assert hasattr(output.data[0], "probs")