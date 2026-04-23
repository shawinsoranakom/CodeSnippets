async def get_admin_listings_with_versions(
    status: prisma.enums.SubmissionStatus | None = None,
    search_query: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> store_model.StoreListingsWithVersionsAdminViewResponse:
    """
    Get store listings for admins with all their versions.

    Args:
        status: Filter by submission status (PENDING, APPROVED, REJECTED)
        search_query: Search by name, description, or user email
        page: Page number for pagination
        page_size: Number of items per page

    Returns:
        Paginated listings with their versions
    """
    logger.debug(
        "Getting admin store listings: "
        f"status={status}, search={search_query}, page={page}"
    )

    # Build the where clause for StoreListing
    store_listing_filter: prisma.types.StoreListingWhereInput = {
        "isDeleted": False,
    }
    if status:
        store_listing_filter["Versions"] = {"some": {"submissionStatus": status}}

    if search_query:
        # Find users with matching email
        matching_users = await prisma.models.User.prisma().find_many(
            where={"email": {"contains": search_query, "mode": "insensitive"}},
        )

        user_ids = [user.id for user in matching_users]

        # Set up OR conditions
        store_listing_filter["OR"] = [
            {"slug": {"contains": search_query, "mode": "insensitive"}},
            {
                "Versions": {
                    "some": {"name": {"contains": search_query, "mode": "insensitive"}}
                }
            },
            {
                "Versions": {
                    "some": {
                        "description": {
                            "contains": search_query,
                            "mode": "insensitive",
                        }
                    }
                }
            },
            {
                "Versions": {
                    "some": {
                        "subHeading": {
                            "contains": search_query,
                            "mode": "insensitive",
                        }
                    }
                }
            },
        ]

        # Add user_id condition if any users matched
        if user_ids:
            store_listing_filter["OR"].append({"owningUserId": {"in": user_ids}})

    # Calculate pagination
    skip = (page - 1) * page_size

    # Create proper Prisma types for the query
    include: prisma.types.StoreListingInclude = {
        "Versions": {
            "order_by": {"version": "desc"},
            "where": {"isDeleted": False},
        },
        "OwningUser": True,
    }

    # Query listings with their versions
    listings = await prisma.models.StoreListing.prisma().find_many(
        where=store_listing_filter,
        skip=skip,
        take=page_size,
        include=include,
        order=[{"createdAt": "desc"}],
    )

    # Get total count for pagination
    total = await prisma.models.StoreListing.prisma().count(where=store_listing_filter)
    total_pages = (total + page_size - 1) // page_size

    # Convert to response models
    listings_with_versions = []
    for listing in listings:
        versions: list[store_model.StoreSubmissionAdminView] = []
        # If we have versions, turn them into StoreSubmissionAdminView models
        for version in listing.Versions or []:
            # .StoreListing is required for StoreSubmission.from_listing_version(v)
            version.StoreListing = listing.model_copy(update={"Versions": None})

            versions.append(
                store_model.StoreSubmissionAdminView.from_listing_version(version)
            )

        # Get the latest version (first in the sorted list)
        latest_version = versions[0] if versions else None

        creator_email = listing.OwningUser.email if listing.OwningUser else None

        listing_with_versions = store_model.StoreListingWithVersionsAdminView(
            listing_id=listing.id,
            slug=listing.slug,
            graph_id=listing.agentGraphId,
            active_listing_version_id=listing.activeVersionId,
            has_approved_version=listing.hasApprovedVersion,
            creator_email=creator_email,
            latest_version=latest_version,
            versions=versions,
        )

        listings_with_versions.append(listing_with_versions)

    logger.debug(f"Found {len(listings_with_versions)} listings for admin")
    return store_model.StoreListingsWithVersionsAdminViewResponse(
        listings=listings_with_versions,
        pagination=store_model.Pagination(
            current_page=page,
            total_items=total,
            total_pages=total_pages,
            page_size=page_size,
        ),
    )