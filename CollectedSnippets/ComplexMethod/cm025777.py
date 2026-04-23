async def async_internal_start_conversation(
        self,
        start_message: str | None = None,
        start_media_id: str | None = None,
        extra_system_prompt: str | None = None,
        preannounce: bool = True,
        preannounce_media_id: str = PREANNOUNCE_URL,
    ) -> None:
        """Start a conversation from the satellite.

        If start_media_id is not provided, message is synthesized to
        audio with the selected pipeline.

        If start_media_id is provided, it is played directly. It is possible
        to omit the message and the satellite will not show any text.

        If preannounce is True, a sound is played before the start message or media.
        If preannounce_media_id is provided, it overrides the default sound.

        Calls async_start_conversation.
        """
        await self._cancel_running_pipeline()

        # The Home Assistant built-in agent doesn't support conversations.
        pipeline = async_get_pipeline(self.hass, self._resolve_pipeline())
        if pipeline.conversation_engine == conversation.HOME_ASSISTANT_AGENT:
            raise HomeAssistantError(
                "Built-in conversation agent does not support starting conversations"
            )

        if start_message is None:
            start_message = ""

        announcement = await self._resolve_announcement_media_id(
            start_message,
            start_media_id,
            preannounce_media_id=preannounce_media_id if preannounce else None,
        )

        if self._is_announcing:
            raise SatelliteBusyError

        self._is_announcing = True
        self._set_state(AssistSatelliteState.RESPONDING)

        # Provide our start info to the LLM so it understands context of incoming message
        if extra_system_prompt is not None:
            self._extra_system_prompt = extra_system_prompt
        else:
            self._extra_system_prompt = start_message or None

        with (
            # Not passing in a conversation ID will force a new one to be created
            chat_session.async_get_chat_session(self.hass) as session,
            conversation.async_get_chat_log(self.hass, session) as chat_log,
        ):
            self._conversation_id = session.conversation_id

            if start_message:
                chat_log.async_add_assistant_content_without_tools(
                    conversation.AssistantContent(
                        agent_id=self.entity_id, content=start_message
                    )
                )

        try:
            await self.async_start_conversation(announcement)
        except Exception:
            # Clear prompt on error
            self._conversation_id = None
            self._extra_system_prompt = None
            raise
        finally:
            self._is_announcing = False
            self._set_state(AssistSatelliteState.IDLE)