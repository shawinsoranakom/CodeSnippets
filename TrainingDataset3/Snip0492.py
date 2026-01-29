def test_get_graph_blocks(
    mocker: pytest_mock.MockFixture,
    snapshot: Snapshot,
) -> None:
    """Test get blocks endpoint"""
    # Mock block
    mock_block = Mock()
    mock_block.to_dict.return_value = {
        "id": "test-block",
        "name": "Test Block",
        "description": "A test block",
        "disabled": False,
    }
    mock_block.id = "test-block"
    mock_block.disabled = False

    # Mock get_blocks
    mocker.patch(
        "backend.api.features.v1.get_blocks",
        return_value={"test-block": lambda: mock_block},
    )

    # Mock block costs
    mocker.patch(
        "backend.data.credit.get_block_cost",
        return_value=[{"cost": 10, "type": "credit"}],
    )

    response = client.get("/blocks")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["id"] == "test-block"

    snapshot.snapshot_dir = "snapshots"
    snapshot.assert_match(
        json.dumps(response_data, indent=2, sort_keys=True),
        "blks_all",
    )
