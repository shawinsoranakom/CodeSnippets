async def get_store_agent_details_as_admin(
    store_listing_version_id: str,
) -> store_model.StoreAgentDetails:
    """Get agent details for admin preview, bypassing the APPROVED-only
    StoreAgent view. Queries StoreListingVersion directly so pending
    submissions are visible."""
    slv = await prisma.models.StoreListingVersion.prisma().find_unique(
        where={"id": store_listing_version_id},
        include={
            "StoreListing": {"include": {"CreatorProfile": True}},
        },
    )
    if not slv or not slv.StoreListing:
        raise NotFoundError(
            f"Store listing version {store_listing_version_id} not found"
        )

    listing = slv.StoreListing
    # CreatorProfile is a required FK relation — should always exist.
    # If it's None, the DB is in a bad state.
    profile = listing.CreatorProfile
    if not profile:
        raise DatabaseError(
            f"StoreListing {listing.id} has no CreatorProfile — FK violated"
        )

    return store_model.StoreAgentDetails(
        store_listing_version_id=slv.id,
        slug=listing.slug,
        agent_name=slv.name,
        agent_video=slv.videoUrl or "",
        agent_output_demo=slv.agentOutputDemoUrl or "",
        agent_image=slv.imageUrls,
        creator=profile.username,
        creator_avatar=profile.avatarUrl or "",
        sub_heading=slv.subHeading,
        description=slv.description,
        instructions=slv.instructions,
        categories=slv.categories,
        runs=0,
        rating=0.0,
        versions=[str(slv.version)],
        graph_id=slv.agentGraphId,
        graph_versions=[str(slv.agentGraphVersion)],
        last_updated=slv.updatedAt,
        recommended_schedule_cron=slv.recommendedScheduleCron,
        active_version_id=listing.activeVersionId or slv.id,
        has_approved_version=listing.hasApprovedVersion,
    )