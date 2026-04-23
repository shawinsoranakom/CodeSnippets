def _format_message(self, message: Any) -> Optional[dict]:
        """Format message for WebSocket transmission

        Args:
            message: Message to format

        Returns:
            Optional[dict]: Formatted message or None if formatting fails
        """

        try:
            if isinstance(message, MultiModalMessage):
                message_dump = message.model_dump()

                message_content = []
                for row in message_dump["content"]:
                    if isinstance(row, dict) and "data" in row:
                        message_content.append(
                            {
                                "url": f"data:image/png;base64,{row['data']}",
                                "alt": "WebSurfer Screenshot",
                            }
                        )
                    else:
                        message_content.append(row)
                message_dump["content"] = message_content

                return {"type": "message", "data": message_dump}

            elif isinstance(message, TeamResult):
                return {
                    "type": "result",
                    "data": message.model_dump(),
                    "status": "complete",
                }
            elif isinstance(message, ModelClientStreamingChunkEvent):
                return {"type": "message_chunk", "data": message.model_dump()}

            elif isinstance(
                message,
                (
                    TextMessage,
                    StopMessage,
                    HandoffMessage,
                    ToolCallRequestEvent,
                    ToolCallExecutionEvent,
                    LLMCallEventMessage,
                ),
            ):
                return {"type": "message", "data": message.model_dump()}

            return None

        except Exception as e:
            logger.error(f"Message formatting error: {e}")
            traceback.print_exc()
            return None