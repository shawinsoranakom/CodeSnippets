async def _async_browse_media_root(self) -> BrowseMedia:
        """Return media browsing root."""
        if not self.coordinator.heos.music_sources:
            try:
                await self.coordinator.heos.get_music_sources()
            except HeosError as error:
                _LOGGER.debug("Unable to load music sources: %s", error)
        children: list[BrowseMedia] = [
            _media_to_browse_media(source)
            for source in self.coordinator.heos.music_sources.values()
            if source.available or source.source_id == heos_const.MUSIC_SOURCE_TUNEIN
        ]
        root = BrowseMedia(
            title="Music Sources",
            media_class=MediaClass.DIRECTORY,
            children_media_class=MediaClass.DIRECTORY,
            media_content_type="",
            media_content_id=BROWSE_ROOT,
            can_expand=True,
            can_play=False,
            children=children,
        )
        # Append media source items
        with suppress(BrowseError):
            browse = await self._async_browse_media_source()
            # If domain is None, it's an overview of available sources
            if browse.domain is None and browse.children:
                children.extend(browse.children)
            else:
                children.append(browse)
        return root