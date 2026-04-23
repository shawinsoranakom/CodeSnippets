async def test_add_to_library_from_store_block_success(mocker):
    """Test successful addition of agent from store to library."""
    block = AddToLibraryFromStoreBlock()

    # Mock the library agent response
    mock_library_agent = MagicMock()
    mock_library_agent.id = "lib-agent-123"
    mock_library_agent.graph_id = "graph-456"
    mock_library_agent.graph_version = 1
    mock_library_agent.name = "Test Agent"

    mocker.patch.object(
        block,
        "_add_to_library",
        return_value=LibraryAgent(
            library_agent_id="lib-agent-123",
            agent_id="graph-456",
            agent_version=1,
            agent_name="Test Agent",
        ),
    )

    input_data = block.Input(
        store_listing_version_id="store-listing-v1", agent_name="Custom Agent Name"
    )

    outputs = {}
    async for name, value in block.run(input_data, user_id="test-user"):
        outputs[name] = value

    assert outputs["success"] is True
    assert outputs["library_agent_id"] == "lib-agent-123"
    assert outputs["agent_id"] == "graph-456"
    assert outputs["agent_version"] == 1
    assert outputs["agent_name"] == "Test Agent"
    assert outputs["message"] == "Agent successfully added to library"