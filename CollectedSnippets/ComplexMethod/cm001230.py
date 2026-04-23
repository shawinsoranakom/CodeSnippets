async def test_get_store_agent_details(mocker):
    # Mock data - StoreAgent view already contains the active version data
    mock_agent = prisma.models.StoreAgent(
        listing_id="test-id",
        listing_version_id="version123",
        slug="test-agent",
        agent_name="Test Agent",
        agent_video="video.mp4",
        agent_image=["image.jpg"],
        featured=False,
        creator_username="creator",
        creator_avatar="avatar.jpg",
        sub_heading="Test heading",
        description="Test description",
        categories=["test"],
        runs=10,
        rating=4.5,
        versions=["1.0"],
        graph_id="test-graph-id",
        graph_versions=["1"],
        updated_at=datetime.now(),
        is_available=True,
        use_for_onboarding=False,
    )

    # Mock StoreAgent prisma call
    mock_store_agent = mocker.patch("prisma.models.StoreAgent.prisma")
    mock_store_agent.return_value.find_first = mocker.AsyncMock(return_value=mock_agent)

    # Call function
    result = await db.get_store_agent_details("creator", "test-agent")

    # Verify results - constructed from the StoreAgent view
    assert result.slug == "test-agent"
    assert result.agent_name == "Test Agent"
    assert result.active_version_id == "version123"
    assert result.has_approved_version is True
    assert result.store_listing_version_id == "version123"
    assert result.graph_id == "test-graph-id"
    assert result.runs == 10
    assert result.rating == 4.5

    # Verify single StoreAgent lookup
    mock_store_agent.return_value.find_first.assert_called_once_with(
        where={"creator_username": "creator", "slug": "test-agent"}
    )