async def edit_store_submission(
    user_id: str,
    store_listing_version_id: str,
    name: str,
    video_url: str | None = None,
    agent_output_demo_url: str | None = None,
    image_urls: list[str] = [],
    description: str = "",
    sub_heading: str = "",
    categories: list[str] = [],
    changes_summary: str | None = "Update submission",
    recommended_schedule_cron: str | None = None,
    instructions: str | None = None,
) -> store_model.StoreSubmission:
    """
    Edit an existing store listing submission.

    Args:
        user_id: ID of the authenticated user editing the submission
        store_listing_version_id: ID of the store listing version to edit
        name: Name of the agent
        video_url: Optional URL to video demo
        image_urls: List of image URLs for the listing
        description: Description of the agent
        sub_heading: Optional sub-heading for the agent
        categories: List of categories for the agent
        changes_summary: Summary of changes made in this submission

    Returns:
        StoreSubmission: The updated store submission

    Raises:
        SubmissionNotFoundError: If the submission is not found
        UnauthorizedError: If the user doesn't own the submission
        InvalidOperationError: If trying to edit a submission that can't be edited
    """
    try:
        # Get the current version and verify ownership
        current_version = await prisma.models.StoreListingVersion.prisma().find_first(
            where=prisma.types.StoreListingVersionWhereInput(
                id=store_listing_version_id
            ),
            include={"StoreListing": True},
        )

        if not current_version:
            raise store_exceptions.SubmissionNotFoundError(
                f"Store listing version not found: {store_listing_version_id}"
            )

        # Verify the user owns this listing (submission)
        if (
            not current_version.StoreListing
            or current_version.StoreListing.owningUserId != user_id
        ):
            raise store_exceptions.UnauthorizedError(
                f"User {user_id} does not own submission {store_listing_version_id}"
            )

        # Only allow editing of PENDING submissions
        if current_version.submissionStatus != prisma.enums.SubmissionStatus.PENDING:
            display_status = current_version.submissionStatus.value.lower()
            raise store_exceptions.InvalidOperationError(
                f"Cannot edit a {display_status} submission. "
                "Only pending submissions can be edited."
            )

        # For PENDING submissions, we can update the existing version
        # Update the existing version
        updated_version = await prisma.models.StoreListingVersion.prisma().update(
            where={"id": store_listing_version_id},
            data=prisma.types.StoreListingVersionUpdateInput(
                name=name,
                videoUrl=video_url,
                agentOutputDemoUrl=agent_output_demo_url,
                imageUrls=image_urls,
                description=description,
                categories=categories,
                subHeading=sub_heading,
                changesSummary=changes_summary,
                recommendedScheduleCron=recommended_schedule_cron,
                instructions=instructions,
            ),
            include={"StoreListing": True},
        )
        if not updated_version:
            raise DatabaseError("Failed to update store listing version")

        logger.debug(
            f"Updated existing listing version {store_listing_version_id} "
            f"for graph {current_version.agentGraphId}"
        )

        return store_model.StoreSubmission.from_listing_version(updated_version)

    except (
        store_exceptions.SubmissionNotFoundError,
        store_exceptions.UnauthorizedError,
        NotFoundError,
        store_exceptions.ListingExistsError,
        store_exceptions.InvalidOperationError,
    ):
        raise
    except prisma.errors.PrismaError as e:
        logger.error(f"Database error editing store submission: {e}")
        raise DatabaseError("Failed to edit store submission") from e