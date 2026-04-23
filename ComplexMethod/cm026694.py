async def _async_update_sources(self, _: Source | None = None) -> None:
        """Get sources for the specific product."""

        # Audio sources
        try:
            # Get all available sources.
            sources = await self._client.get_available_sources(target_remote=False)

        # Use a fallback list of sources
        except ValueError:
            # Try to get software version from device
            if self.device_info:
                sw_version = self.device_info.get("sw_version")
            if not sw_version:
                sw_version = self._software_status.software_version

            _LOGGER.warning(
                "The API is outdated compared to the device software version %s and %s. Using fallback sources",
                MOZART_API_VERSION,
                sw_version,
            )
            sources = FALLBACK_SOURCES

        # Save all of the relevant enabled sources, both the ID and the friendly name for displaying in a dict.
        self._audio_sources = {
            source.id: source.name
            for source in cast(list[Source], sources.items)
            if source.is_enabled and source.id and source.name and source.is_playable
        }

        # Some sources are not Beolink expandable, meaning that they can't be joined by
        # or expand to other Bang & Olufsen devices for a multi-room experience.
        # _source_change, which is used throughout the entity for current source
        # information, lacks this information, so source ID's and their expandability is
        # stored in the self._beolink_sources variable.
        self._beolink_sources = {
            source.id: (
                source.is_multiroom_available
                if source.is_multiroom_available is not None
                else False
            )
            for source in cast(list[Source], sources.items)
            if source.id
        }

        # Video sources from remote menu
        menu_items = await self._client.get_remote_menu()

        for key in menu_items:
            menu_item = menu_items[key]

            if not menu_item.available:
                continue

            # TV SOURCES
            if (
                menu_item.content is not None
                and menu_item.content.categories
                and len(menu_item.content.categories) > 0
                and "music" not in menu_item.content.categories
                and menu_item.label
                and menu_item.label != "TV"
            ):
                self._video_sources[key] = menu_item.label
                self._video_source_id_map[
                    menu_item.content.content_uri.removeprefix("tv://")
                ] = menu_item.label

        # Combine the source dicts
        self._sources = self._audio_sources | self._video_sources

        self._attr_source_list = list(self._sources.values())

        # HASS won't necessarily be running the first time this method is run
        if self.hass.is_running:
            self.async_write_ha_state()