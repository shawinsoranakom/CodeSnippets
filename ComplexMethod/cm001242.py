async def create_store_submission(
    user_id: str,
    graph_id: str,
    graph_version: int,
    slug: str,
    name: str,
    video_url: str | None = None,
    agent_output_demo_url: str | None = None,
    image_urls: list[str] = [],
    description: str = "",
    instructions: str | None = None,
    sub_heading: str = "",
    categories: list[str] = [],
    changes_summary: str | None = "Initial Submission",
    recommended_schedule_cron: str | None = None,
) -> store_model.StoreSubmission:
    """
    Create the first (and only) store listing and thus submission as a normal user

    Args:
        user_id: ID of the authenticated user submitting the listing
        graph_id: ID of the agent graph being submitted
        graph_version: Version of the agent graph being submitted
        slug: URL slug for the listing
        name: Name of the agent
        video_url: Optional URL to video demo
        image_urls: List of image URLs for the listing
        description: Description of the agent
        sub_heading: Optional sub-heading for the agent
        categories: List of categories for the agent
        changes_summary: Summary of changes made in this submission

    Returns:
        StoreSubmission: The created store submission
    """
    logger.debug(
        f"Creating store submission for user #{user_id}, "
        f"graph #{graph_id} v{graph_version}"
    )

    try:
        # Sanitize slug to only allow letters and hyphens
        slug = "".join(
            c if c.isalpha() or c == "-" or c.isnumeric() else "" for c in slug
        ).lower()

        # First verify the agent graph belongs to this user
        graph = await prisma.models.AgentGraph.prisma().find_first(
            where={"id": graph_id, "version": graph_version, "userId": user_id},
            include={"User": {"include": {"Profile": True}}},
        )

        if not graph:
            logger.warning(
                f"Agent graph {graph_id} v{graph_version} not found for user {user_id}"
            )
            # Provide more user-friendly error message when graph_id is empty
            if not graph_id or graph_id.strip() == "":
                raise ValueError(
                    "No agent selected. "
                    "Please select an agent before submitting to the store."
                )
            else:
                raise NotFoundError(
                    f"Agent #{graph_id} v{graph_version} not found "
                    f"for this user (#{user_id})"
                )

        if not graph.User or not graph.User.Profile:
            logger.warning(f"User #{user_id} does not have a Profile")
            raise PreconditionFailed(
                "User must create a Marketplace Profile before submitting an agent"
            )

        async with transaction() as tx:
            # Determine next version number for this listing
            existing_listing = await prisma.models.StoreListing.prisma(tx).find_unique(
                where={"agentGraphId": graph_id},
                include={
                    "Versions": {
                        # We just need the latest version and one of each status:
                        "order_by": {"version": "desc"},
                        "distinct": ["submissionStatus"],
                        "where": {"isDeleted": False},
                    }
                },
            )
            next_version = 1
            graph_has_pending_submissions = False
            if existing_listing and existing_listing.Versions:
                current_latest_version = max(
                    (slv.version for slv in existing_listing.Versions), default=0
                )
                next_version = current_latest_version + 1

                graph_has_pending_submissions = any(
                    slv.submissionStatus == prisma.enums.SubmissionStatus.PENDING
                    for slv in existing_listing.Versions
                )

            # Delete any currently PENDING submissions for the same graph
            # in favor of the new submission
            if graph_has_pending_submissions:
                await prisma.models.StoreListingVersion.prisma(tx).update_many(
                    where={
                        "agentGraphId": graph.id,
                        "submissionStatus": prisma.enums.SubmissionStatus.PENDING,
                        "isDeleted": False,
                    },
                    data={"isDeleted": True},
                )

            new_submission = await prisma.models.StoreListingVersion.prisma(tx).create(
                data={
                    "AgentGraph": {
                        "connect": {
                            "graphVersionId": {
                                "id": graph_id,
                                "version": graph_version,
                            }
                        }
                    },
                    "name": name,
                    "version": next_version,
                    "videoUrl": video_url,
                    "agentOutputDemoUrl": agent_output_demo_url,
                    "imageUrls": image_urls,
                    "description": description,
                    "instructions": instructions,
                    "categories": categories,
                    "subHeading": sub_heading,
                    "submissionStatus": prisma.enums.SubmissionStatus.PENDING,
                    "submittedAt": datetime.now(tz=timezone.utc),
                    "changesSummary": changes_summary,
                    "recommendedScheduleCron": recommended_schedule_cron,
                    "StoreListing": {
                        "connect_or_create": {
                            "where": {"agentGraphId": graph_id},
                            "create": {
                                "slug": slug,
                                "agentGraphId": graph_id,
                                "OwningUser": {"connect": {"id": user_id}},
                                "CreatorProfile": {"connect": {"userId": user_id}},
                            },
                        }
                    },
                },
                include={"StoreListing": True},
            )

        if not new_submission:
            raise DatabaseError("Failed to create store listing version")

        logger.debug(f"Created store listing for agent {graph_id}")
        return store_model.StoreSubmission.from_listing_version(new_submission)
    except prisma.errors.UniqueViolationError as exc:
        # Attempt to check if the error was due to the slug field being unique
        error_str = str(exc)
        if "slug" in error_str.lower():
            logger.debug(f"Slug '{slug}' is already in use by graph #{graph_id}")
            raise store_exceptions.SlugAlreadyInUseError(
                f"The slug '{slug}' is already in use by another one of your agents. "
                "Please choose a different slug."
            ) from exc
        else:
            # Reraise as a generic database error for other unique violations
            raise DatabaseError(
                f"Unique constraint violated (not slug): {error_str}"
            ) from exc
    except (
        NotFoundError,
        store_exceptions.ListingExistsError,
    ):
        raise
    except prisma.errors.PrismaError as e:
        logger.error(f"Database error creating store submission: {e}")
        raise DatabaseError("Failed to create store submission") from e