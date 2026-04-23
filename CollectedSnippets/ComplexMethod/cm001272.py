async def test_preview_queries_store_listing_version_not_store_agent() -> None:
    """get_store_agent_details_as_admin must query StoreListingVersion
    directly (not the APPROVED-only StoreAgent view). This is THE test that
    prevents the bypass from being accidentally reverted."""
    from backend.api.features.store.db import get_store_agent_details_as_admin

    mock_slv = MagicMock()
    mock_slv.id = SLV_ID
    mock_slv.name = "Test Agent"
    mock_slv.subHeading = "Short desc"
    mock_slv.description = "Long desc"
    mock_slv.videoUrl = None
    mock_slv.agentOutputDemoUrl = None
    mock_slv.imageUrls = ["https://example.com/img.png"]
    mock_slv.instructions = None
    mock_slv.categories = ["productivity"]
    mock_slv.version = 1
    mock_slv.agentGraphId = GRAPH_ID
    mock_slv.agentGraphVersion = GRAPH_VERSION
    mock_slv.updatedAt = datetime(2026, 3, 24, tzinfo=timezone.utc)
    mock_slv.recommendedScheduleCron = "0 9 * * *"

    mock_listing = MagicMock()
    mock_listing.id = "listing-id"
    mock_listing.slug = "test-agent"
    mock_listing.activeVersionId = SLV_ID
    mock_listing.hasApprovedVersion = False
    mock_listing.CreatorProfile = MagicMock(username="creator", avatarUrl="")
    mock_slv.StoreListing = mock_listing

    with (
        patch(
            "backend.api.features.store.db.prisma.models" ".StoreListingVersion.prisma",
        ) as mock_slv_prisma,
        patch(
            "backend.api.features.store.db.prisma.models.StoreAgent.prisma",
        ) as mock_store_agent_prisma,
    ):
        mock_slv_prisma.return_value.find_unique = AsyncMock(return_value=mock_slv)

        result = await get_store_agent_details_as_admin(SLV_ID)

    # Verify it queried StoreListingVersion (not the APPROVED-only StoreAgent)
    mock_slv_prisma.return_value.find_unique.assert_awaited_once()
    await_args = mock_slv_prisma.return_value.find_unique.await_args
    assert await_args is not None
    assert await_args.kwargs["where"] == {"id": SLV_ID}

    # Verify the APPROVED-only StoreAgent view was NOT touched
    mock_store_agent_prisma.assert_not_called()

    # Verify the result has the right data
    assert result.agent_name == "Test Agent"
    assert result.agent_image == ["https://example.com/img.png"]
    assert result.has_approved_version is False
    assert result.runs == 0
    assert result.rating == 0.0