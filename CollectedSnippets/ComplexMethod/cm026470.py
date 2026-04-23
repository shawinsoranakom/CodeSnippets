def _parse_status(self) -> None:
        """Parse status."""
        status: dict[str, Any] | None = self._ps4.status
        if status is not None:
            self._games = load_games(self.hass, cast(str, self.unique_id))
            if self._games:
                self.get_source_list()

            self._retry = 0
            self._disconnected = False
            if status.get("status") == "Ok":
                title_id = status.get("running-app-titleid")
                name = status.get("running-app-name")

                if title_id and name is not None:
                    self._attr_state = MediaPlayerState.PLAYING

                    if self.media_content_id != title_id:
                        self._attr_media_content_id = title_id
                        if self._use_saved():
                            _LOGGER.debug("Using saved data for media: %s", title_id)
                            return

                        self._attr_media_title = name
                        self._attr_source = self._attr_media_title
                        self._attr_media_content_type = None
                        # Get data from PS Store.
                        self.hass.async_create_background_task(
                            self.async_get_title_data(title_id, name),
                            "ps4.media_player-get_title_data",
                        )
                elif self.state != MediaPlayerState.IDLE:
                    self.idle()
            elif self.state != MediaPlayerState.OFF:
                self.state_standby()

        elif self._retry > DEFAULT_RETRIES:
            self.state_unknown()
        else:
            self._retry += 1