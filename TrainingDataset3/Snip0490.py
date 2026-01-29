def test_ask_otto_with_graph_data(
    mocker: pytest_mock.MockFixture,
    snapshot: Snapshot,
) -> None:
    """Test Otto API request with graph data included"""
    # Mock the OttoService.ask method
    mock_response = otto_models.ApiResponse(
        answer="Here's information about your graph.",
        documents=[
            otto_models.Document(
                url="https://example.com/graph-doc",
                relevance_score=0.92,
            ),
        ],
        success=True,
    )

    mocker.patch.object(
        OttoService,
        "ask",
        return_value=mock_response,
    )

    request_data = {
        "query": "Tell me about my graph",
        "conversation_history": [],
        "message_id": "msg_456",
        "include_graph_data": True,
        "graph_id": "graph_123",
    }

    response = client.post("/ask", json=request_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

    # Snapshot test the response
    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "otto_grph",
    )
