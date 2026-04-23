async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media."""
        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = play_item.url

        if self.state == MediaPlayerState.OFF:
            await self.async_turn_on()

        if media_id:
            parts = media_id.split(":")

            if parts[0] == "list":
                if (index := parts[3]) == "-1":
                    index = "0"

                await self.coordinator.musiccast.play_list_media(index, self._zone_id)
                return

            if parts[0] == "presets":
                index = parts[1]
                await self.coordinator.musiccast.recall_netusb_preset(
                    self._zone_id, index
                )
                return

            if parts[0] in ("http", "https") or media_id.startswith("/"):
                media_id = async_process_play_media_url(self.hass, media_id)

                await self.coordinator.musiccast.play_url_media(
                    self._zone_id, media_id, "HomeAssistant"
                )
                return

        raise HomeAssistantError(
            "Only presets, media from media browser and http URLs are supported"
        )