async def _async_send_text_only_message(
        self,
        targets: list[str],
        message: str,
        title: str | None,
        thread_ts: str | None,
        *,
        username: str | None = None,
        icon: str | None = None,
        blocks: Any | None = None,
    ) -> None:
        """Send a text-only message."""
        message_dict: MessageT = {"link_names": True, "text": message}

        if username:
            message_dict["username"] = username

        if icon:
            if icon.lower().startswith(("http://", "https://")):
                message_dict["icon_url"] = icon
            else:
                message_dict["icon_emoji"] = icon

        if blocks:
            message_dict["blocks"] = blocks

        if thread_ts:
            message_dict["thread_ts"] = thread_ts

        tasks = {
            target: self._client.chat_postMessage(**message_dict, channel=target)
            for target in targets
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for target, result in zip(tasks, results, strict=False):
            if isinstance(result, SlackApiError):
                _LOGGER.error(
                    "There was a Slack API error while sending to %s: %r",
                    target,
                    result,
                )
            elif isinstance(result, ClientError):
                _LOGGER.error("Error while sending message to %s: %r", target, result)