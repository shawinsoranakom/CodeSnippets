def new_media_status(self, media_status):
        """Handle updates of the media status."""
        if (
            media_status
            and media_status.player_is_idle
            and media_status.idle_reason == "ERROR"
        ):
            external_url = None
            internal_url = None
            url_description = ""
            with suppress(NoURLAvailableError):  # external_url not configured
                external_url = get_url(self.hass, allow_internal=False)

            with suppress(NoURLAvailableError):  # internal_url not configured
                internal_url = get_url(self.hass, allow_external=False)

            if media_status.content_id:
                if external_url and media_status.content_id.startswith(external_url):
                    url_description = f" from external_url ({external_url})"
                if internal_url and media_status.content_id.startswith(internal_url):
                    url_description = f" from internal_url ({internal_url})"

            _LOGGER.error(
                (
                    "Failed to cast media %s%s. Please make sure the URL is: "
                    "Reachable from the cast device and either a publicly resolvable "
                    "hostname or an IP address"
                ),
                media_status.content_id,
                url_description,
            )

        self.media_status = media_status
        self.media_status_received = dt_util.utcnow()
        self.schedule_update_ha_state()