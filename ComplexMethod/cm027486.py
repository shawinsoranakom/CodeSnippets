async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return details about the media source.

        This renders the multi-level album structure for an account, its albums,
        or the contents of an album. This will return a BrowseMediaSource with a
        single level of children at the next level of the hierarchy.
        """
        if not item.identifier:
            # Top level view that lists all accounts.
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=None,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaClass.IMAGE,
                title="Google Photos",
                can_play=False,
                can_expand=True,
                children_media_class=MediaClass.DIRECTORY,
                children=[
                    _build_account(entry, PhotosIdentifier(cast(str, entry.unique_id)))
                    for entry in self._async_config_entries()
                ],
            )

        # Determine the configuration entry for this item
        identifier = PhotosIdentifier.of(item.identifier)
        entry = self._async_config_entry(identifier.config_entry_id)
        coordinator = entry.runtime_data
        client = coordinator.client

        source = _build_account(entry, identifier)
        if identifier.id_type is None:
            albums = await coordinator.list_albums()
            source.children = [
                _build_album(
                    album.title,
                    PhotosIdentifier.album(
                        identifier.config_entry_id,
                        album.id,
                    ),
                    _cover_photo_url(album, THUMBNAIL_SIZE),
                )
                for album in albums
            ]
            return source

        if (
            identifier.id_type != PhotosIdentifierType.ALBUM
            or identifier.media_id is None
        ):
            raise BrowseError(f"Unsupported identifier: {identifier}")

        media_items: list[MediaItem] = []
        try:
            async for media_item_result in await client.list_media_items(
                album_id=identifier.media_id, page_size=MEDIA_ITEMS_PAGE_SIZE
            ):
                media_items.extend(media_item_result.media_items)
        except GooglePhotosApiError as err:
            raise BrowseError(f"Error listing media items: {err}") from err

        source.children = [
            _build_media_item(
                PhotosIdentifier.photo(identifier.config_entry_id, media_item.id),
                media_item,
            )
            for media_item in media_items
        ]
        return source