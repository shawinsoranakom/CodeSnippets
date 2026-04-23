async def _async_build_immich(
        self, item: MediaSourceItem, entries: list[ConfigEntry]
    ) -> list[BrowseMediaSource]:
        """Handle browsing different immich instances."""

        # --------------------------------------------------------
        # root level, render immich instances
        # --------------------------------------------------------
        if not item.identifier:
            LOGGER.debug("Render all Immich instances")
            return [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=entry.unique_id,
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title=entry.title,
                    can_play=False,
                    can_expand=True,
                )
                for entry in entries
            ]

        # --------------------------------------------------------
        # 1st level, render collections overview
        # --------------------------------------------------------
        identifier = ImmichMediaSourceIdentifier(item.identifier)
        entry: ImmichConfigEntry | None = (
            self.hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, identifier.unique_id
            )
        )
        assert entry
        immich_api = entry.runtime_data.api

        if identifier.collection is None:
            LOGGER.debug("Render all collections for %s", entry.title)
            return [
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=f"{identifier.unique_id}|{collection}",
                    media_class=MediaClass.DIRECTORY,
                    media_content_type=MediaClass.IMAGE,
                    title=collection.split("|", maxsplit=1)[0],
                    can_play=False,
                    can_expand=True,
                )
                for collection in ("albums", "favorites|favorites", "people", "tags")
            ]

        # --------------------------------------------------------
        # 2nd level, render collection
        # --------------------------------------------------------
        if identifier.collection_id is None:
            if identifier.collection == "albums":
                LOGGER.debug("Render all albums for %s", entry.title)
                try:
                    albums = await immich_api.albums.async_get_all_albums()
                except ImmichError:
                    return []

                return [
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"{identifier.unique_id}|albums|{album.album_id}",
                        media_class=MediaClass.DIRECTORY,
                        media_content_type=MediaClass.IMAGE,
                        title=album.album_name,
                        can_play=False,
                        can_expand=True,
                        thumbnail=f"/immich/{identifier.unique_id}/{album.album_thumbnail_asset_id}/thumbnail/image/jpg",
                    )
                    for album in albums
                ]

            if identifier.collection == "tags":
                LOGGER.debug("Render all tags for %s", entry.title)
                try:
                    tags = await immich_api.tags.async_get_all_tags()
                except ImmichError:
                    return []

                return [
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"{identifier.unique_id}|tags|{tag.tag_id}",
                        media_class=MediaClass.DIRECTORY,
                        media_content_type=MediaClass.IMAGE,
                        title=tag.name,
                        can_play=False,
                        can_expand=True,
                    )
                    for tag in tags
                ]

            if identifier.collection == "people":
                LOGGER.debug("Render all people for %s", entry.title)
                try:
                    people = await immich_api.people.async_get_all_people()
                except ImmichError:
                    return []

                return [
                    BrowseMediaSource(
                        domain=DOMAIN,
                        identifier=f"{identifier.unique_id}|people|{person.person_id}",
                        media_class=MediaClass.DIRECTORY,
                        media_content_type=MediaClass.IMAGE,
                        title=person.name,
                        can_play=False,
                        can_expand=True,
                        thumbnail=f"/immich/{identifier.unique_id}/{person.person_id}/person/image/jpg",
                    )
                    for person in people
                ]

        # --------------------------------------------------------
        # final level, render assets
        # --------------------------------------------------------
        assert identifier.collection_id is not None
        assets: list[ImmichAsset] = []
        if identifier.collection == "albums":
            LOGGER.debug(
                "Render all assets of album %s for %s",
                identifier.collection_id,
                entry.title,
            )
            try:
                album_info = await immich_api.albums.async_get_album_info(
                    identifier.collection_id
                )
                assets = album_info.assets
            except ImmichError:
                return []

        elif identifier.collection == "tags":
            LOGGER.debug(
                "Render all assets with tag %s",
                identifier.collection_id,
            )
            try:
                assets = await immich_api.search.async_get_all_by_tag_ids(
                    [identifier.collection_id]
                )
            except ImmichError:
                return []

        elif identifier.collection == "people":
            LOGGER.debug(
                "Render all assets for person %s",
                identifier.collection_id,
            )
            try:
                assets = await immich_api.search.async_get_all_by_person_ids(
                    [identifier.collection_id]
                )
            except ImmichError:
                return []
        elif identifier.collection == "favorites":
            LOGGER.debug("Render all assets for favorites collection")
            try:
                assets = await immich_api.search.async_get_all_favorites()
            except ImmichError:
                return []

        ret: list[BrowseMediaSource] = []
        for asset in assets:
            if not (mime_type := asset.original_mime_type) or not mime_type.startswith(
                ("image/", "video/")
            ):
                continue

            if mime_type.startswith("image/"):
                media_class = MediaClass.IMAGE
                can_play = False
                thumb_mime_type = mime_type
            else:
                media_class = MediaClass.VIDEO
                can_play = True
                thumb_mime_type = "image/jpeg"

            ret.append(
                BrowseMediaSource(
                    domain=DOMAIN,
                    identifier=(
                        f"{identifier.unique_id}|"
                        f"{identifier.collection}|"
                        f"{identifier.collection_id}|"
                        f"{asset.asset_id}|"
                        f"{asset.original_file_name}|"
                        f"{mime_type}"
                    ),
                    media_class=media_class,
                    media_content_type=mime_type,
                    title=asset.original_file_name,
                    can_play=can_play,
                    can_expand=False,
                    thumbnail=f"/immich/{identifier.unique_id}/{asset.asset_id}/thumbnail/{thumb_mime_type}",
                )
            )

        return ret