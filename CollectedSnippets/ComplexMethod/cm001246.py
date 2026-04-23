async def _approve_sub_agent(
    tx,
    sub_graph: prisma.models.AgentGraph,
    main_agent_name: str,
    main_agent_graph_version: int,
    main_agent_user_id: str,
) -> None:
    """Approve a single sub-agent by creating/updating store listings as needed"""
    heading = f"Sub-agent of {main_agent_name} v{main_agent_graph_version}"

    # Find existing listing for this sub-agent
    listing = await prisma.models.StoreListing.prisma(tx).find_first(
        where={"agentGraphId": sub_graph.id, "isDeleted": False},
        include={"Versions": True},
    )

    # Early return: Create new listing if none exists
    if not listing:
        await prisma.models.StoreListing.prisma(tx).create(
            data=prisma.types.StoreListingCreateInput(
                slug=f"sub-agent-{sub_graph.id[:8]}",
                agentGraphId=sub_graph.id,
                owningUserId=main_agent_user_id,
                hasApprovedVersion=True,
                Versions={
                    "create": [
                        _create_sub_agent_version_data(
                            sub_graph, heading, main_agent_name
                        )
                    ]
                },
            )
        )
        return

    # Find version matching this sub-graph
    matching_version = next(
        (
            v
            for v in listing.Versions or []
            if v.agentGraphId == sub_graph.id
            and v.agentGraphVersion == sub_graph.version
        ),
        None,
    )

    # Early return: Approve existing version if found and not already approved
    if matching_version:
        if matching_version.submissionStatus == prisma.enums.SubmissionStatus.APPROVED:
            return  # Already approved, nothing to do

        await prisma.models.StoreListingVersion.prisma(tx).update(
            where={"id": matching_version.id},
            data={
                "submissionStatus": prisma.enums.SubmissionStatus.APPROVED,
                "reviewedAt": datetime.now(tz=timezone.utc),
            },
        )
        await prisma.models.StoreListing.prisma(tx).update(
            where={"id": listing.id}, data={"hasApprovedVersion": True}
        )
        return

    # Create new version if no matching version found
    next_version = max((v.version for v in listing.Versions or []), default=0) + 1
    await prisma.models.StoreListingVersion.prisma(tx).create(
        data={
            **_create_sub_agent_version_data(sub_graph, heading, main_agent_name),
            "version": next_version,
            "storeListingId": listing.id,
        }
    )
    await prisma.models.StoreListing.prisma(tx).update(
        where={"id": listing.id}, data={"hasApprovedVersion": True}
    )