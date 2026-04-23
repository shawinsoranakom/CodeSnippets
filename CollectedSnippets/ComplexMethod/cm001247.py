async def _send_submission_review_notification(
    creator_user_id: str,
    is_approved: bool,
    external_comments: str,
    reviewed_listing_version: prisma.models.StoreListingVersion,
):
    """Send email notification to the agent creator"""
    reviewer = (
        reviewed_listing_version.Reviewer if reviewed_listing_version.Reviewer else None
    )

    base_url = settings.config.frontend_base_url or settings.config.platform_base_url

    if is_approved:
        store_agent = await prisma.models.StoreAgent.prisma().find_first_or_raise(
            where={"listing_version_id": reviewed_listing_version.id}
        )

        # Send approval notification
        creator_username = store_agent.creator_username
        notification_data = AgentApprovalData(
            agent_name=reviewed_listing_version.name,
            graph_id=reviewed_listing_version.agentGraphId,
            graph_version=reviewed_listing_version.agentGraphVersion,
            reviewer_name=(
                reviewer.name if reviewer and reviewer.name else DEFAULT_ADMIN_NAME
            ),
            reviewer_email=(reviewer.email if reviewer else DEFAULT_ADMIN_EMAIL),
            comments=external_comments,
            reviewed_at=(
                reviewed_listing_version.reviewedAt or datetime.now(tz=timezone.utc)
            ),
            store_url=(
                f"{base_url}/marketplace/agent/{creator_username}/{store_agent.slug}"
            ),
        )

        notification_event = NotificationEventModel[AgentApprovalData](
            user_id=creator_user_id,
            type=prisma.enums.NotificationType.AGENT_APPROVED,
            data=notification_data,
        )
    else:
        # Send rejection notification
        graph_id = reviewed_listing_version.agentGraphId
        notification_data = AgentRejectionData(
            agent_name=reviewed_listing_version.name,
            graph_id=reviewed_listing_version.agentGraphId,
            graph_version=reviewed_listing_version.agentGraphVersion,
            reviewer_name=(
                reviewer.name if reviewer and reviewer.name else DEFAULT_ADMIN_NAME
            ),
            reviewer_email=(reviewer.email if reviewer else DEFAULT_ADMIN_EMAIL),
            comments=external_comments,
            reviewed_at=reviewed_listing_version.reviewedAt
            or datetime.now(tz=timezone.utc),
            resubmit_url=f"{base_url}/build?flowID={graph_id}",
        )

        notification_event = NotificationEventModel[AgentRejectionData](
            user_id=creator_user_id,
            type=prisma.enums.NotificationType.AGENT_REJECTED,
            data=notification_data,
        )

    # Queue the notification for immediate sending
    await queue_notification_async(notification_event)
    logger.info(
        f"Queued {'approval' if is_approved else 'rejection'} notification "
        f"for agent '{reviewed_listing_version.name}' of user #{creator_user_id}"
    )