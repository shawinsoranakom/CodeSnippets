async def review_store_submission(
    store_listing_version_id: str,
    is_approved: bool,
    external_comments: str,
    internal_comments: str,
    reviewer_id: str,
) -> store_model.StoreSubmissionAdminView:
    """Review a store listing submission as an admin."""
    try:
        submission = await prisma.models.StoreListingVersion.prisma().find_unique(
            where={"id": store_listing_version_id},
            include={"AgentGraph": {"include": AGENT_GRAPH_INCLUDE}},
        )

        if not submission:
            raise NotFoundError(
                f"Store listing version {store_listing_version_id} not found"
            )
        assert submission.AgentGraph is not None
        creator_user_id = submission.AgentGraph.userId

        # Check if we're rejecting an already approved agent
        is_rejecting_approved = (
            not is_approved
            and submission.submissionStatus == prisma.enums.SubmissionStatus.APPROVED
        )

        # If approving, update the listing to indicate it has an approved version
        if is_approved:
            async with transaction() as tx:
                # Handle sub-agent approvals in transaction
                await asyncio.gather(
                    *[
                        _approve_sub_agent(
                            tx,
                            sub_graph,
                            submission.name,
                            submission.agentGraphVersion,
                            creator_user_id,
                        )
                        for sub_graph in await get_sub_graphs(submission.AgentGraph)
                    ]
                )

                # Update the AgentGraph with store listing data
                await prisma.models.AgentGraph.prisma(tx).update(
                    where={
                        "graphVersionId": {
                            "id": submission.agentGraphId,
                            "version": submission.agentGraphVersion,
                        }
                    },
                    data={
                        "name": submission.name,
                        "description": submission.description,
                        "recommendedScheduleCron": submission.recommendedScheduleCron,
                        "instructions": submission.instructions,
                    },
                )

                # Generate embedding for approved listing (best-effort)
                try:
                    await ensure_embedding(
                        version_id=store_listing_version_id,
                        name=submission.name,
                        description=submission.description,
                        sub_heading=submission.subHeading,
                        categories=submission.categories,
                        tx=tx,
                    )
                except Exception as emb_err:
                    logger.warning(
                        f"Could not generate embedding for listing "
                        f"{store_listing_version_id}: {emb_err}"
                    )

                await prisma.models.StoreListing.prisma(tx).update(
                    where={"id": submission.storeListingId},
                    data={
                        "hasApprovedVersion": True,
                        "ActiveVersion": {"connect": {"id": store_listing_version_id}},
                    },
                )

        # If rejecting an approved agent, update the StoreListing accordingly
        if is_rejecting_approved:
            # Check if there are other approved versions
            other_approved = (
                await prisma.models.StoreListingVersion.prisma().find_first(
                    where={
                        "storeListingId": submission.storeListingId,
                        "id": {"not": store_listing_version_id},
                        "submissionStatus": prisma.enums.SubmissionStatus.APPROVED,
                    }
                )
            )

            if not other_approved:
                # No other approved versions, update hasApprovedVersion to False
                await prisma.models.StoreListing.prisma().update(
                    where={"id": submission.storeListingId},
                    data={
                        "hasApprovedVersion": False,
                        "ActiveVersion": {"disconnect": True},
                    },
                )
            else:
                # Set the most recent other approved version as active
                await prisma.models.StoreListing.prisma().update(
                    where={"id": submission.storeListingId},
                    data={
                        "ActiveVersion": {"connect": {"id": other_approved.id}},
                    },
                )

        submission_status = (
            prisma.enums.SubmissionStatus.APPROVED
            if is_approved
            else prisma.enums.SubmissionStatus.REJECTED
        )

        # Update the version with review information
        update_data: prisma.types.StoreListingVersionUpdateInput = {
            "submissionStatus": submission_status,
            "reviewedAt": datetime.now(tz=timezone.utc),
            "Reviewer": {"connect": {"id": reviewer_id}},
            "reviewComments": external_comments,
            "internalComments": internal_comments,
        }

        # Update the version
        reviewed_submission = await prisma.models.StoreListingVersion.prisma().update(
            where={"id": store_listing_version_id},
            data=update_data,
            include={
                "StoreListing": True,  # required for StoreSubmissionAdminView
                "Reviewer": True,  # used in _send_submission_review_notification
            },
        )

        if not reviewed_submission:
            raise DatabaseError(
                f"Failed to update store listing version {store_listing_version_id}"
            )

        try:
            await _send_submission_review_notification(
                creator_user_id,
                is_approved,
                external_comments,
                reviewed_submission,
            )
        except Exception as e:
            logger.error(f"Failed to send email notification for agent review: {e}")
            # Don't fail the review process if email sending fails

        return store_model.StoreSubmissionAdminView.from_listing_version(
            reviewed_submission
        )

    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Could not create store submission review: {e}")
        raise DatabaseError("Failed to create store submission review") from e