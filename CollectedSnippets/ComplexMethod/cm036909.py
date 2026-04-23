def test_completion_request_batched(server: RemoteOpenAIServer, model_name: str):
    N = 10

    # test input: list[str]
    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": [input_text] * N},
    )
    output = ClassificationResponse.model_validate(classification_response.json())

    assert len(output.data) == N
    for i, item in enumerate(output.data):
        assert item.index == i
        assert hasattr(item, "label")
        assert hasattr(item, "probs")
        assert len(item.probs) == item.num_classes
        assert item.label in ["Default", "Spoiled"]

    # test input: list[list[int]]
    classification_response = requests.post(
        server.url_for("classify"),
        json={"model": model_name, "input": [input_tokens] * N},
    )
    output = ClassificationResponse.model_validate(classification_response.json())

    assert len(output.data) == N
    for i, item in enumerate(output.data):
        assert item.index == i
        assert hasattr(item, "label")
        assert hasattr(item, "probs")
        assert len(item.probs) == item.num_classes
        assert item.label in ["Default", "Spoiled"]