def test_get_graphs(
    mocker: pytest_mock.MockFixture,
    snapshot: Snapshot,
    test_user_id: str,
) -> None:
    """Test get graphs endpoint"""
    mock_graph = GraphModel(
        id="graph-123",
        version=1,
        is_active=True,
        name="Test Graph",
        description="A test graph",
        user_id=test_user_id,
        created_at=datetime(2025, 9, 4, 13, 37),
    )

    mocker.patch(
        "backend.data.graph.list_graphs_paginated",
        return_value=Mock(graphs=[mock_graph]),
    )

    response = client.get("/graphs")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["id"] == "graph-123"

    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "grphs_all",
    )
