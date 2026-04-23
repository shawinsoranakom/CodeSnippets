async def _async_build_diskstations(
        self, item: MediaSourceItem
    ) -> list[BrowseMediaSource]:
        """Handle browsing different diskstations."""
        if not item.identifier:
            return [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=entry.unique_id,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title=f"{entry.title} - {entry.unique_id}",
                    can_play=False,
                    can_expand=True,
                )
                for entry in self.entries
            ]
        identifier = SynologyPhotosMediaSourceIdentifier(item.identifier)
        entry: SynologyDSMConfigEntry | None = (
            self.hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, identifier.unique_id
            )
        )
        if TYPE_CHECKING:
            assert entry
        diskstation = entry.runtime_data
        if TYPE_CHECKING:
            assert diskstation.api.photos is not None

        if identifier.album_id is None:
            # Get Albums
            try:
                albums = await diskstation.api.photos.get_albums()
            except SynologyDSMException:
                return []
            if TYPE_CHECKING:
                assert albums is not None

            ret = [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{item.identifier}/0",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title="All images",
                    can_play=False,
                    can_expand=True,
                )
            ]
            ret += [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{item.identifier}/shared",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title="Shared space",
                    can_play=False,
                    can_expand=True,
                )
            ]
            ret.extend(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{item.identifier}/{album.album_id}_{album.passphrase}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title=album.name,
                    can_play=False,
                    can_expand=True,
                )
                for album in albums
            )

            return ret

        # Request items of album
        # Get Items
        if identifier.album_id == "shared":
            # Get items from shared space
            try:
                album_items = await diskstation.api.photos.get_items_from_shared_space(
                    0, 1000
                )
            except SynologyDSMException:
                return []
        else:
            album = SynoPhotosAlbum(
                int(identifier.album_id), "", 0, identifier.passphrase
            )
            try:
                album_items = await diskstation.api.photos.get_items_from_album(
                    album, 0, 1000
                )
            except SynologyDSMException:
                return []
        if TYPE_CHECKING:
            assert album_items is not None

        ret = []
        for album_item in album_items:
            mime_type, _ = mimetypes.guess_type(album_item.file_name)
            if isinstance(mime_type, str) and mime_type.startswith("image/"):
                # Force small small thumbnails
                album_item.thumbnail_size = "sm"
                suffix = ""
                if album_item.is_shared:
                    suffix = SHARED_SUFFIX
                ret.append(
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=(
                            f"{identifier.unique_id}/"
                            f"{identifier.album_id}_{identifier.passphrase}/"
                            f"{album_item.thumbnail_cache_key}/"
                            f"{album_item.file_name}{suffix}"
                        ),
                        media_class=MediaClass.IMAGE,
                        media_content_type=mime_type,
                        title=album_item.file_name,
                        can_play=True,
                        can_expand=False,
                        thumbnail=await self.async_get_thumbnail(
                            album_item, diskstation
                        ),
                    )
                )
        return ret