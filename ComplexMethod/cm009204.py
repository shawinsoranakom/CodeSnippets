def test_responses_stream_normalizes_in_memory_prompt_cache_retention(
    event_index: int, event_type: type
) -> None:
    """`prompt_cache_retention="in_memory"` from the API must not abort streams.

    The API emits the underscore form while older `openai` packages declare only
    `"in-memory"` in the Literal (openai-python#2883). `_coerce_chunk_response`
    should normalize so both the `response.created` and `response.completed`
    handlers can validate successfully.
    """
    stream = copy.deepcopy(responses_stream)
    target = stream[event_index]
    assert isinstance(target, event_type)
    assert isinstance(target, (ResponseCreatedEvent, ResponseCompletedEvent))
    dumped = target.response.model_dump(mode="json")
    dumped["prompt_cache_retention"] = "in_memory"
    target.response = dumped  # type: ignore[assignment]

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
    # The completed event drives usage/metadata aggregation, so assert it
    # survived coercion when that branch is exercised.
    if event_type is ResponseCompletedEvent:
        assert full.usage_metadata is not None