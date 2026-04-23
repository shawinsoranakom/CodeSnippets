def test__construct_lc_result_from_responses_api_file_search_response() -> None:
    """Test a response with file search output."""
    response = Response(
        id="resp_123",
        created_at=1234567890,
        model="gpt-4o",
        object="response",
        parallel_tool_calls=True,
        tools=[],
        tool_choice="auto",
        output=[
            ResponseFileSearchToolCall(
                id="filesearch_123",
                type="file_search_call",
                status="completed",
                queries=["python code", "langchain"],
                results=[
                    Result(
                        file_id="file_123",
                        filename="example.py",
                        score=0.95,
                        text="def hello_world() -> None:\n    print('Hello, world!')",
                        attributes={"language": "python", "size": 42},
                    )
                ],
            )
        ],
    )

    # v0
    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    assert "tool_outputs" in result.generations[0].message.additional_kwargs
    assert len(result.generations[0].message.additional_kwargs["tool_outputs"]) == 1
    assert (
        result.generations[0].message.additional_kwargs["tool_outputs"][0]["type"]
        == "file_search_call"
    )
    assert (
        result.generations[0].message.additional_kwargs["tool_outputs"][0]["id"]
        == "filesearch_123"
    )
    assert (
        result.generations[0].message.additional_kwargs["tool_outputs"][0]["status"]
        == "completed"
    )
    assert result.generations[0].message.additional_kwargs["tool_outputs"][0][
        "queries"
    ] == ["python code", "langchain"]
    assert (
        len(
            result.generations[0].message.additional_kwargs["tool_outputs"][0][
                "results"
            ]
        )
        == 1
    )
    assert (
        result.generations[0].message.additional_kwargs["tool_outputs"][0]["results"][
            0
        ]["file_id"]
        == "file_123"
    )
    assert (
        result.generations[0].message.additional_kwargs["tool_outputs"][0]["results"][
            0
        ]["score"]
        == 0.95
    )

    # responses/v1
    result = _construct_lc_result_from_responses_api(response)
    assert result.generations[0].message.content == [
        {
            "type": "file_search_call",
            "id": "filesearch_123",
            "status": "completed",
            "queries": ["python code", "langchain"],
            "results": [
                {
                    "file_id": "file_123",
                    "filename": "example.py",
                    "score": 0.95,
                    "text": "def hello_world() -> None:\n    print('Hello, world!')",
                    "attributes": {"language": "python", "size": 42},
                }
            ],
        }
    ]