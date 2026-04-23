def test_responses_stream_tolerates_dict_response_field() -> None:
    """Regression test for `AttributeError: 'dict' object has no attribute 'id'`.

    The OpenAI SDK types `<event>.response` strictly as `Response`, but raw dicts
    have been observed in the wild.
    """
    stream = copy.deepcopy(responses_stream)
    first_event = stream[0]
    assert isinstance(first_event, ResponseCreatedEvent)
    first_event.response = first_event.response.model_dump(mode="json")  # type: ignore[assignment]
    assert isinstance(first_event.response, dict)

    llm = ChatOpenAI(model=MODEL, use_responses_api=True)
    mock_client = MagicMock()

    def mock_create(*args: Any, **kwargs: Any) -> MockSyncContextManager:
        return MockSyncContextManager(stream)

    mock_client.responses.create = mock_create

    full: BaseMessageChunk | None = None
    with patch.object(llm, "root_client", mock_client):
        for chunk in llm.stream("test"):
            assert isinstance(chunk, AIMessageChunk)
            full = chunk if full is None else full + chunk
    assert isinstance(full, AIMessageChunk)
    assert full.id == "resp_123"