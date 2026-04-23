async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task."""
        attachments: list[LLMImageAttachment] | None = None
        if task.attachments:
            attachments = await async_prepare_image_generation_attachments(
                self.hass, task.attachments
            )

        try:
            if attachments is None:
                image = await self._cloud.llm.async_generate_image(
                    prompt=task.instructions,
                )
            else:
                image = await self._cloud.llm.async_edit_image(
                    prompt=task.instructions,
                    attachments=attachments,
                )
        except LLMAuthenticationError as err:
            raise HomeAssistantError("Cloud LLM authentication failed") from err
        except LLMRateLimitError as err:
            raise HomeAssistantError("Cloud LLM is rate limited") from err
        except LLMResponseError as err:
            raise HomeAssistantError(str(err)) from err
        except LLMServiceError as err:
            raise HomeAssistantError("Error talking to Cloud LLM") from err
        except LLMError as err:
            raise HomeAssistantError(str(err)) from err

        return ai_task.GenImageTaskResult(
            conversation_id=chat_log.conversation_id,
            mime_type=image["mime_type"],
            image_data=image["image_data"],
            model=image.get("model"),
            width=image.get("width"),
            height=image.get("height"),
            revised_prompt=image.get("revised_prompt"),
        )