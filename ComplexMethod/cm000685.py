async def test_get_store_agent_details_block_success(mocker):
    """Test successful retrieval of store agent details."""
    block = GetStoreAgentDetailsBlock()

    mocker.patch.object(
        block,
        "_get_agent_details",
        return_value=StoreAgentDetails(
            found=True,
            store_listing_version_id="version-123",
            agent_name="Test Agent",
            description="A test agent for testing",
            creator="Test Creator",
            categories=["productivity", "automation"],
            runs=100,
            rating=4.5,
        ),
    )

    input_data = block.Input(creator="Test Creator", slug="test-slug")
    outputs = {}
    async for name, value in block.run(input_data):
        outputs[name] = value

    assert outputs["found"] is True
    assert outputs["store_listing_version_id"] == "version-123"
    assert outputs["agent_name"] == "Test Agent"
    assert outputs["description"] == "A test agent for testing"
    assert outputs["creator"] == "Test Creator"
    assert outputs["categories"] == ["productivity", "automation"]
    assert outputs["runs"] == 100
    assert outputs["rating"] == 4.5