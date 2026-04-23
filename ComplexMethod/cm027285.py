async def _async_send_remote_file_message(
        self,
        url: str,
        targets: list[str],
        message: str,
        title: str | None,
        thread_ts: str | None,
        *,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Upload a remote file (with message) to Slack."""
        if not self._hass.config.is_allowed_external_url(url):
            _LOGGER.error("URL is not allowed: %s", url)
            return

        filename = _async_get_filename_from_url(url)
        session = aiohttp_client.async_get_clientsession(self._hass)

        # Fetch the remote file
        kwargs: AuthDictT = {}
        if username and password:
            kwargs = {"auth": BasicAuth(username, password=password)}

        try:
            async with session.get(url, **kwargs) as resp:
                resp.raise_for_status()
                file_content = await resp.read()
        except ClientError as err:
            _LOGGER.error("Error while retrieving %s: %r", url, err)
            return

        channel_ids = [await self._async_get_channel_id(target) for target in targets]
        channel_ids = [cid for cid in channel_ids if cid]  # Remove None values

        if not channel_ids:
            _LOGGER.error("No valid channel IDs resolved for targets: %s", targets)
            return

        await upload_file_to_slack(
            client=self._client,
            channel_ids=channel_ids,
            file_content=file_content,
            filename=filename,
            title=title,
            message=message,
            thread_ts=thread_ts,
        )