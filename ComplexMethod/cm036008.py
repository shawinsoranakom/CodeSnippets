async def from_payload(
        cls,
        payload: dict,
        slack_team_store,
    ) -> 'SlackMessageView | None':
        """Create a view from a raw Slack payload.

        This factory method handles the various payload formats from different
        Slack interactions (events, form submissions, block suggestions).

        Args:
            payload: Raw Slack payload dictionary
            slack_team_store: Store for retrieving bot tokens

        Returns:
            SlackMessageView if all required fields are available,
            None if required fields are missing or bot token unavailable.
        """
        from openhands.core.logger import openhands_logger as logger

        team_id = payload.get('team', {}).get('id') or payload.get('team_id')
        channel_id = (
            payload.get('container', {}).get('channel_id')
            or payload.get('channel', {}).get('id')
            or payload.get('channel_id')
        )
        user_id = payload.get('user', {}).get('id') or payload.get('slack_user_id')
        message_ts = payload.get('message_ts', '')
        thread_ts = payload.get('thread_ts')

        if not team_id or not channel_id or not user_id:
            logger.warning(
                'slack_message_view_from_payload_missing_fields',
                extra={
                    'has_team_id': bool(team_id),
                    'has_channel_id': bool(channel_id),
                    'has_user_id': bool(user_id),
                    'payload_keys': list(payload.keys()),
                },
            )
            return None

        bot_token = await slack_team_store.get_team_bot_token(team_id)
        if not bot_token:
            logger.warning(
                'slack_message_view_from_payload_no_bot_token',
                extra={'team_id': team_id},
            )
            return None

        return cls(
            bot_access_token=bot_token,
            slack_user_id=user_id,
            channel_id=channel_id,
            message_ts=message_ts,
            thread_ts=thread_ts,
            team_id=team_id,
        )