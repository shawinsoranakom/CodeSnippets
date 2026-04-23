def _update_from_coordinator(self):
        if self._tv.on:
            if self._tv.powerstate in ("Standby", "StandbyKeep"):
                self._attr_state = MediaPlayerState.OFF
            else:
                self._attr_state = MediaPlayerState.ON
        else:
            self._attr_state = MediaPlayerState.OFF

        self._sources = {
            srcid: source.get("name") or f"Source {srcid}"
            for srcid, source in (self._tv.sources or {}).items()
        }

        self._attr_source = self._sources.get(self._tv.source_id)
        self._attr_source_list = list(self._sources.values())

        self._attr_app_id = self._tv.application_id
        if app := self._tv.applications.get(self._tv.application_id):
            self._attr_app_name = app.get("label")
        else:
            self._attr_app_name = None

        self._attr_volume_level = self._tv.volume
        self._attr_is_volume_muted = self._tv.muted

        if self._tv.channel_active:
            self._attr_media_content_type = MediaType.CHANNEL
            self._attr_media_content_id = f"all/{self._tv.channel_id}"
            self._attr_media_title = self._tv.channels.get(self._tv.channel_id, {}).get(
                "name"
            )
            self._attr_media_channel = self._attr_media_title
        elif self._tv.application_id:
            self._attr_media_content_type = MediaType.APP
            self._attr_media_content_id = self._tv.application_id
            self._attr_media_title = self._tv.applications.get(
                self._tv.application_id, {}
            ).get("label")
            self._attr_media_channel = None
        else:
            self._attr_media_content_type = None
            self._attr_media_content_id = None
            self._attr_media_title = self._sources.get(self._tv.source_id)
            self._attr_media_channel = None

        self._attr_assumed_state = True