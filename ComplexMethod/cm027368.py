async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        _LOGGER.debug("Call play media type <%s>, Id <%s>", media_type, media_id)

        if media_type == MediaType.CHANNEL and self._client.tv_state.channels:
            _LOGGER.debug("Searching channel")
            partial_match_channel_id = None
            perfect_match_channel_id = None

            for channel in self._client.tv_state.channels:
                if media_id == channel["channelNumber"]:
                    perfect_match_channel_id = channel["channelId"]
                    continue

                if media_id.lower() == channel["channelName"].lower():
                    perfect_match_channel_id = channel["channelId"]
                    continue

                if media_id.lower() in channel["channelName"].lower():
                    partial_match_channel_id = channel["channelId"]

            if perfect_match_channel_id is not None:
                _LOGGER.debug(
                    "Switching to channel <%s> with perfect match",
                    perfect_match_channel_id,
                )
                await self._client.set_channel(perfect_match_channel_id)
            elif partial_match_channel_id is not None:
                _LOGGER.debug(
                    "Switching to channel <%s> with partial match",
                    partial_match_channel_id,
                )
                await self._client.set_channel(partial_match_channel_id)