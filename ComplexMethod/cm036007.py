async def create_slack_view_from_payload(
        message: Message, slack_user: SlackUser | None, saas_user_auth: UserAuth | None
    ):
        payload = message.message
        slack_user_id = payload['slack_user_id']
        channel_id = payload.get('channel_id')
        message_ts = payload.get('message_ts')
        thread_ts = payload.get('thread_ts')
        team_id = payload['team_id']
        user_msg = payload.get('user_msg')

        bot_access_token = await slack_team_store.get_team_bot_token(team_id)
        if not bot_access_token:
            logger.error(
                'Did not find slack team',
                extra={
                    'slack_user_id': slack_user_id,
                    'channel_id': channel_id,
                },
            )
            raise Exception('Did not find slack team')

        # Determine if this is a known slack user by openhands
        # Return SlackMessageView (not SlackViewInterface) for unauthenticated users
        if not slack_user or not saas_user_auth or not channel_id or not message_ts:
            return SlackMessageView(
                bot_access_token=bot_access_token,
                slack_user_id=slack_user_id,
                channel_id=channel_id or '',
                message_ts=message_ts or '',
                thread_ts=thread_ts,
                team_id=team_id,
            )

        # At this point, we've verified slack_user, saas_user_auth, channel_id, and message_ts are set
        # user_msg should always be present in Slack payloads
        if not user_msg:
            raise ValueError('user_msg is required but was not provided in payload')
        assert channel_id is not None
        assert message_ts is not None

        conversation = await asyncio.wait_for(
            SlackFactory.determine_if_updating_existing_conversation(message),
            timeout=GENERAL_TIMEOUT,
        )
        if conversation:
            logger.info(
                'Found existing slack conversation',
                extra={
                    'conversation_id': conversation.conversation_id,
                    'parent_id': conversation.parent_id,
                },
            )
            return SlackUpdateExistingConversationView(
                bot_access_token=bot_access_token,
                user_msg=user_msg,
                slack_user_id=slack_user_id,
                slack_to_openhands_user=slack_user,
                saas_user_auth=saas_user_auth,
                channel_id=channel_id,
                message_ts=message_ts,
                thread_ts=thread_ts,
                selected_repo=None,
                should_extract=True,
                send_summary_instruction=True,
                conversation_id=conversation.conversation_id,
                slack_conversation=conversation,
                team_id=team_id,
                v1_enabled=False,
            )

        elif SlackFactory.did_user_select_repo_from_form(message):
            return SlackNewConversationFromRepoFormView(
                bot_access_token=bot_access_token,
                user_msg=user_msg,
                slack_user_id=slack_user_id,
                slack_to_openhands_user=slack_user,
                saas_user_auth=saas_user_auth,
                channel_id=channel_id,
                message_ts=message_ts,
                thread_ts=thread_ts,
                selected_repo=payload['selected_repo'],
                should_extract=True,
                send_summary_instruction=True,
                conversation_id='',
                team_id=team_id,
                v1_enabled=False,
            )

        else:
            return SlackNewConversationView(
                bot_access_token=bot_access_token,
                user_msg=user_msg,
                slack_user_id=slack_user_id,
                slack_to_openhands_user=slack_user,
                saas_user_auth=saas_user_auth,
                channel_id=channel_id,
                message_ts=message_ts,
                thread_ts=thread_ts,
                selected_repo=None,
                should_extract=True,
                send_summary_instruction=True,
                conversation_id='',
                team_id=team_id,
                v1_enabled=False,
            )