async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate image task."""
        await self._async_handle_chat_log(chat_log, task.name, force_image=True)

        if not isinstance(chat_log.content[-1], conversation.AssistantContent):
            raise HomeAssistantError(
                "Last content in chat log is not an AssistantContent"
            )

        image_call: ImageGenerationCall | None = None
        for content in reversed(chat_log.content):
            if not isinstance(content, conversation.AssistantContent):
                break
            if isinstance(content.native, ImageGenerationCall):
                if image_call is None or image_call.result is None:
                    image_call = content.native
                else:  # Remove image data from chat log to save memory
                    content.native.result = None

        if image_call is None or image_call.result is None:
            raise HomeAssistantError("No image returned")

        image_data = base64.b64decode(image_call.result)
        image_call.result = None

        if hasattr(image_call, "output_format") and (
            output_format := image_call.output_format
        ):
            mime_type = f"image/{output_format}"
        else:
            mime_type = "image/png"

        if hasattr(image_call, "size") and (size := image_call.size):
            width, height = tuple(size.split("x"))
        else:
            width, height = None, None

        return ai_task.GenImageTaskResult(
            image_data=image_data,
            conversation_id=chat_log.conversation_id,
            mime_type=mime_type,
            width=int(width) if width else None,
            height=int(height) if height else None,
            model=self.subentry.data.get(CONF_IMAGE_MODEL, RECOMMENDED_IMAGE_MODEL),
            revised_prompt=image_call.revised_prompt
            if hasattr(image_call, "revised_prompt")
            else None,
        )