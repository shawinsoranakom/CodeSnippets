async def create_store_listing(
    db: Prisma,
    graph_id: str,
    graph_version: int,
    metadata: dict,
) -> None:
    """Create StoreListing and StoreListingVersion for an agent."""
    listing_id = metadata["listing_id"]
    version_id = metadata["store_listing_version_id"]

    # Check if listing already exists
    existing_listing = await db.storelisting.find_unique(where={"id": listing_id})
    if existing_listing:
        print(f"  Store listing {listing_id} already exists, skipping")
        return

    print(f"  Creating store listing: {metadata['agent_name']}")

    # Determine if this should be approved
    is_approved = metadata["is_available"]
    submission_status = (
        prisma.enums.SubmissionStatus.APPROVED
        if is_approved
        else prisma.enums.SubmissionStatus.PENDING
    )

    # Create the store listing first (without activeVersionId - will update after)
    await db.storelisting.create(
        data=StoreListingCreateInput(
            id=listing_id,
            slug=metadata["slug"],
            agentGraphId=graph_id,
            agentGraphVersion=graph_version,
            owningUserId=AUTOGPT_USER_ID,
            hasApprovedVersion=is_approved,
            useForOnboarding=metadata["use_for_onboarding"],
        )
    )

    # Create the store listing version
    await db.storelistingversion.create(
        data=StoreListingVersionCreateInput(
            id=version_id,
            version=1,
            agentGraphId=graph_id,
            agentGraphVersion=graph_version,
            name=metadata["agent_name"],
            subHeading=metadata["sub_heading"],
            videoUrl=metadata["agent_video"],
            imageUrls=metadata["agent_image"],
            description=metadata["description"],
            categories=metadata["categories"],
            isFeatured=metadata["featured"],
            isAvailable=metadata["is_available"],
            submissionStatus=submission_status,
            submittedAt=datetime.now() if is_approved else None,
            reviewedAt=datetime.now() if is_approved else None,
            storeListingId=listing_id,
        )
    )

    # Update the store listing with the active version if approved
    if is_approved:
        await db.storelisting.update(
            where={"id": listing_id},
            data={"ActiveVersion": {"connect": {"id": version_id}}},
        )
