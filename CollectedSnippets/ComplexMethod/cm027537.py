async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        if not self._tv.on:
            raise BrowseError("Can't browse when tv is turned off")

        if media_content_id is None or media_content_id == "":
            return await self.async_browse_media_root()
        path = media_content_id.partition("/")
        if path[0] == "channels":
            return await self.async_browse_media_channels(True)
        if path[0] == "applications":
            return await self.async_browse_media_applications(True)
        if path[0] == "favorite_lists":
            return await self.async_browse_media_favorite_lists(True)
        if path[0] == "favorites":
            return await self.async_browse_media_favorites(path[2], True)

        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")