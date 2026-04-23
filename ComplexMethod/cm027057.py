async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task."""
        # Get the user prompt from the chat log
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)

        model = self.subentry.data.get(CONF_CHAT_MODEL, RECOMMENDED_IMAGE_MODEL)
        prompt_parts: list[PartUnionDict] = [user_message.content]
        if user_message.attachments:
            prompt_parts.extend(
                await async_prepare_files_for_prompt(
                    self.hass,
                    self._genai_client,
                    [(a.path, a.mime_type) for a in user_message.attachments],
                )
            )

        try:
            response = await self._genai_client.aio.models.generate_content(
                model=model,
                contents=prompt_parts,
                config=GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )
        except (APIError, ValueError) as err:
            LOGGER.error("Error generating image: %s", err)
            raise HomeAssistantError(f"Error generating image: {err}") from err

        if response.prompt_feedback:
            raise HomeAssistantError(
                f"Error generating content due to content violations, reason: {response.prompt_feedback.block_reason_message}"
            )

        if (
            not response.candidates
            or not response.candidates[0].content
            or not response.candidates[0].content.parts
        ):
            raise HomeAssistantError("Unknown error generating image")

        # Parse response
        response_text = ""
        response_image: Part | None = None
        for part in response.candidates[0].content.parts:
            if (
                part.inline_data
                and part.inline_data.data
                and part.inline_data.mime_type
                and part.inline_data.mime_type.startswith("image/")
            ):
                if response_image is None:
                    response_image = part
                else:
                    LOGGER.warning("Prompt generated multiple images")
            elif isinstance(part.text, str) and not part.thought:
                response_text += part.text

        if response_image is None:
            raise HomeAssistantError("Response did not include image")

        assert response_image.inline_data is not None
        assert response_image.inline_data.data is not None
        assert response_image.inline_data.mime_type is not None

        image_data = response_image.inline_data.data
        mime_type = response_image.inline_data.mime_type

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=response_text,
            )
        )

        return ai_task.GenImageTaskResult(
            image_data=image_data,
            conversation_id=chat_log.conversation_id,
            mime_type=mime_type,
            model=model.partition("/")[-1],
        )