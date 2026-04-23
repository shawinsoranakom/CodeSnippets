def test_delete_graph(
    mocker: pytest_mock.MockFixture,
    snapshot: Snapshot,
    test_user_id: str,
) -> None:
    """Test delete graph endpoint"""
    # Mock active graph for deactivation
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
        "backend.api.features.v1.graph_db.get_graph",
        return_value=mock_graph,
    )
    mocker.patch(
        "backend.api.features.v1.on_graph_deactivate",
        return_value=None,
    )
    mocker.patch(
        "backend.api.features.v1.graph_db.delete_graph",
        return_value=3,  # Number of versions deleted
    )

    response = client.delete("/graphs/graph-123")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["version_counts"] == 3

    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "grphs_del",
    )
