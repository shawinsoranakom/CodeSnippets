def handle_insufficient_funds_notif(
    db_client: "DatabaseManagerClient",
    user_id: str,
    graph_id: str,
    e: InsufficientBalanceError,
) -> None:
    # Check if we've already sent a notification for this user+agent combo.
    # We only send one notification per user per agent until they top up credits.
    redis_key = f"{INSUFFICIENT_FUNDS_NOTIFIED_PREFIX}:{user_id}:{graph_id}"
    try:
        redis_client = redis.get_redis()
        # SET NX returns True only if the key was newly set (didn't exist)
        is_new_notification = redis_client.set(
            redis_key,
            "1",
            nx=True,
            ex=INSUFFICIENT_FUNDS_NOTIFIED_TTL_SECONDS,
        )
        if not is_new_notification:
            # Already notified for this user+agent, skip all notifications
            logger.debug(
                f"Skipping duplicate insufficient funds notification for "
                f"user={user_id}, graph={graph_id}"
            )
            return
    except Exception as redis_error:
        # If Redis fails, log and continue to send the notification
        # (better to occasionally duplicate than to never notify)
        logger.warning(
            f"Failed to check/set insufficient funds notification flag in Redis: "
            f"{redis_error}"
        )

    shortfall = abs(e.amount) - e.balance
    metadata = db_client.get_graph_metadata(graph_id)
    base_url = settings.config.frontend_base_url or settings.config.platform_base_url

    # Queue user email notification
    queue_notification(
        NotificationEventModel(
            user_id=user_id,
            type=NotificationType.ZERO_BALANCE,
            data=ZeroBalanceData(
                current_balance=e.balance,
                billing_page_link=f"{base_url}/profile/credits",
                shortfall=shortfall,
                agent_name=metadata.name if metadata else "Unknown Agent",
            ),
        )
    )

    # Send Discord system alert
    try:
        user_email = db_client.get_user_email_by_id(user_id)

        alert_message = (
            f"❌ **Insufficient Funds Alert**\n"
            f"User: {user_email or user_id}\n"
            f"Agent: {metadata.name if metadata else 'Unknown Agent'}\n"
            f"Current balance: ${e.balance / 100:.2f}\n"
            f"Attempted cost: ${abs(e.amount) / 100:.2f}\n"
            f"Shortfall: ${abs(shortfall) / 100:.2f}\n"
            f"[View User Details]({base_url}/admin/spending?search={user_email})"
        )

        get_notification_manager_client().discord_system_alert(
            alert_message, DiscordChannel.PRODUCT
        )
    except Exception as alert_error:
        logger.error(f"Failed to send insufficient funds Discord alert: {alert_error}")