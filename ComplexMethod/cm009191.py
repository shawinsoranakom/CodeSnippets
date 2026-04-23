def test__construct_lc_result_from_responses_api_mixed_search_responses() -> None:
    """Test a response with both web search and file search outputs."""

    response = Response(
        id="resp_123",
        created_at=1234567890,
        model="gpt-4o",
        object="response",
        parallel_tool_calls=True,
        tools=[],
        tool_choice="auto",
        output=[
            ResponseOutputMessage(
                type="message",
                id="msg_123",
                content=[
                    ResponseOutputText(
                        type="output_text", text="Here's what I found:", annotations=[]
                    )
                ],
                role="assistant",
                status="completed",
            ),
            ResponseFunctionWebSearch(
                id="websearch_123",
                type="web_search_call",
                status="completed",
                action=ActionSearch(type="search", query="search query"),
            ),
            ResponseFileSearchToolCall(
                id="filesearch_123",
                type="file_search_call",
                status="completed",
                queries=["python code"],
                results=[
                    Result(
                        file_id="file_123",
                        filename="example.py",
                        score=0.95,
                        text="def hello_world() -> None:\n    print('Hello, world!')",
                    )
                ],
            ),
        ],
    )

    # v0
    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    # Check message content
    assert result.generations[0].message.content == [
        {"type": "text", "text": "Here's what I found:", "annotations": []}
    ]

    # Check tool outputs
    assert "tool_outputs" in result.generations[0].message.additional_kwargs
    assert len(result.generations[0].message.additional_kwargs["tool_outputs"]) == 2

    # Check web search output
    web_search = next(
        output
        for output in result.generations[0].message.additional_kwargs["tool_outputs"]
        if output["type"] == "web_search_call"
    )
    assert web_search["id"] == "websearch_123"
    assert web_search["status"] == "completed"

    # Check file search output
    file_search = next(
        output
        for output in result.generations[0].message.additional_kwargs["tool_outputs"]
        if output["type"] == "file_search_call"
    )
    assert file_search["id"] == "filesearch_123"
    assert file_search["queries"] == ["python code"]
    assert file_search["results"][0]["filename"] == "example.py"

    # responses/v1
    result = _construct_lc_result_from_responses_api(response)
    assert result.generations[0].message.content == [
        {
            "type": "text",
            "text": "Here's what I found:",
            "annotations": [],
            "id": "msg_123",
        },
        {
            "type": "web_search_call",
            "id": "websearch_123",
            "status": "completed",
            "action": {"type": "search", "query": "search query"},
        },
        {
            "type": "file_search_call",
            "id": "filesearch_123",
            "queries": ["python code"],
            "results": [
                {
                    "file_id": "file_123",
                    "filename": "example.py",
                    "score": 0.95,
                    "text": "def hello_world() -> None:\n    print('Hello, world!')",
                }
            ],
            "status": "completed",
        },
    ]