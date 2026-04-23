def test_responses_stream(output_version: str, expected_content: list[dict]) -> None:
    llm = ChatOpenAI(model=MODEL, use_responses_api=True, output_version=output_version)
    mock_client = MagicMock()

    def mock_create(*args: Any, **kwargs: Any) -> MockSyncContextManager:
        return MockSyncContextManager(responses_stream)

    mock_client.responses.create = mock_create

    full: BaseMessageChunk | None = None
    chunks = []
    with patch.object(llm, "root_client", mock_client):
        for chunk in llm.stream("test"):
            assert isinstance(chunk, AIMessageChunk)
            full = chunk if full is None else full + chunk
            chunks.append(chunk)
    assert isinstance(full, AIMessageChunk)

    assert full.content == expected_content
    assert full.additional_kwargs == {}
    assert full.id == "resp_123"

    # Test reconstruction
    payload = llm._get_request_payload([full])
    completed = [
        item
        for item in responses_stream
        if item.type == "response.completed"  # type: ignore[attr-defined]
    ]
    assert len(completed) == 1
    response = completed[0].response  # type: ignore[attr-defined]

    assert len(response.output) == len(payload["input"])
    for idx, item in enumerate(response.output):
        dumped = _strip_none(item.model_dump())
        _ = dumped.pop("status", None)
        assert dumped == payload["input"][idx]