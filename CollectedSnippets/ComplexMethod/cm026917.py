async def _handle_trigger_result(
        self,
        result: SentenceTriggerResult,
        user_input: ConversationInput,
        chat_log: ChatLog,
    ) -> str:
        """Run sentence trigger callbacks and return response text."""
        manager = get_agent_manager(self.hass)

        # Gather callback responses in parallel
        trigger_callbacks = [
            trigger_callback(user_input, trigger_result)
            for trigger_intent_name, trigger_result in result.matched_triggers.items()
            if (trigger_callback := manager.get_trigger_callback(trigger_intent_name))
            is not None
        ]

        tool_input = llm.ToolInput(
            tool_name="trigger_sentence",
            tool_args={},
            external=True,
        )
        chat_log.async_add_assistant_content_without_tools(
            AssistantContent(
                agent_id=user_input.agent_id,
                content=None,
                tool_calls=[tool_input],
            )
        )

        # Use first non-empty result as response.
        #
        # There may be multiple copies of a trigger running when editing in
        # the UI, so it's critical that we filter out empty responses here.
        response_text = ""
        response_set_by_trigger = False
        for trigger_future in asyncio.as_completed(trigger_callbacks):
            trigger_response = await trigger_future
            if trigger_response is None:
                continue

            response_text = trigger_response
            response_set_by_trigger = True
            break

        if response_set_by_trigger:
            # Response was explicitly set to empty
            response_text = response_text or ""
        elif not response_text:
            # Use translated acknowledgment for pipeline language
            language = user_input.language or self.hass.config.language
            translations = await translation.async_get_translations(
                self.hass, language, DOMAIN, [DOMAIN]
            )
            response_text = translations.get(
                f"component.{DOMAIN}.conversation.agent.done", "Done"
            )

        tool_result: dict[str, Any] = {"response": response_text}
        chat_log.async_add_assistant_content_without_tools(
            ToolResultContent(
                agent_id=user_input.agent_id,
                tool_call_id=tool_input.id,
                tool_name=tool_input.tool_name,
                tool_result=tool_result,
            )
        )

        return response_text