async def update_user_notification_preference(
    user_id: str, data: NotificationPreferenceDTO
) -> NotificationPreference:
    try:
        update_data: UserUpdateInput = {}
        if data.email:
            update_data["email"] = data.email
        if NotificationType.AGENT_RUN in data.preferences:
            update_data["notifyOnAgentRun"] = data.preferences[
                NotificationType.AGENT_RUN
            ]
        if NotificationType.ZERO_BALANCE in data.preferences:
            update_data["notifyOnZeroBalance"] = data.preferences[
                NotificationType.ZERO_BALANCE
            ]
        if NotificationType.LOW_BALANCE in data.preferences:
            update_data["notifyOnLowBalance"] = data.preferences[
                NotificationType.LOW_BALANCE
            ]
        if NotificationType.BLOCK_EXECUTION_FAILED in data.preferences:
            update_data["notifyOnBlockExecutionFailed"] = data.preferences[
                NotificationType.BLOCK_EXECUTION_FAILED
            ]
        if NotificationType.CONTINUOUS_AGENT_ERROR in data.preferences:
            update_data["notifyOnContinuousAgentError"] = data.preferences[
                NotificationType.CONTINUOUS_AGENT_ERROR
            ]
        if NotificationType.DAILY_SUMMARY in data.preferences:
            update_data["notifyOnDailySummary"] = data.preferences[
                NotificationType.DAILY_SUMMARY
            ]
        if NotificationType.WEEKLY_SUMMARY in data.preferences:
            update_data["notifyOnWeeklySummary"] = data.preferences[
                NotificationType.WEEKLY_SUMMARY
            ]
        if NotificationType.MONTHLY_SUMMARY in data.preferences:
            update_data["notifyOnMonthlySummary"] = data.preferences[
                NotificationType.MONTHLY_SUMMARY
            ]
        if NotificationType.AGENT_APPROVED in data.preferences:
            update_data["notifyOnAgentApproved"] = data.preferences[
                NotificationType.AGENT_APPROVED
            ]
        if NotificationType.AGENT_REJECTED in data.preferences:
            update_data["notifyOnAgentRejected"] = data.preferences[
                NotificationType.AGENT_REJECTED
            ]
        if data.daily_limit:
            update_data["maxEmailsPerDay"] = data.daily_limit

        user = await PrismaUser.prisma().update(
            where={"id": user_id},
            data=update_data,
        )
        if not user:
            raise ValueError(f"User not found with ID: {user_id}")

        # Invalidate cache for this user since notification preferences are part of user data
        get_user_by_id.cache_delete(user_id)

        preferences: dict[NotificationType, bool] = {
            NotificationType.AGENT_RUN: user.notifyOnAgentRun or True,
            NotificationType.ZERO_BALANCE: user.notifyOnZeroBalance or True,
            NotificationType.LOW_BALANCE: user.notifyOnLowBalance or True,
            NotificationType.BLOCK_EXECUTION_FAILED: user.notifyOnBlockExecutionFailed
            or True,
            NotificationType.CONTINUOUS_AGENT_ERROR: user.notifyOnContinuousAgentError
            or True,
            NotificationType.DAILY_SUMMARY: user.notifyOnDailySummary or True,
            NotificationType.WEEKLY_SUMMARY: user.notifyOnWeeklySummary or True,
            NotificationType.MONTHLY_SUMMARY: user.notifyOnMonthlySummary or True,
            NotificationType.AGENT_APPROVED: user.notifyOnAgentApproved or True,
            NotificationType.AGENT_REJECTED: user.notifyOnAgentRejected or True,
        }
        notification_preference = NotificationPreference(
            user_id=user.id,
            email=user.email,
            preferences=preferences,
            daily_limit=user.maxEmailsPerDay or 3,
            # TODO with other changes later, for now we just will email them
            emails_sent_today=0,
            last_reset_date=datetime.now(),
        )
        return NotificationPreference.model_validate(notification_preference)

    except Exception as e:
        raise DatabaseError(
            f"Failed to update user notification preference for user {user_id}: {e}"
        ) from e