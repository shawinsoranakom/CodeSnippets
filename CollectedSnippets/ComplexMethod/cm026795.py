async def _build_media_path(
        self,
        config: MotionEyeConfigEntry,
        device: dr.DeviceEntry,
        kind: str,
        path: str,
    ) -> BrowseMediaSource:
        """Build the media sources for media kinds."""
        base = self._build_media_kind(config, device, kind)

        parsed_path = PurePath(path)
        if path != "/":
            base.title += f" {PurePath(*parsed_path.parts[1:])}"

        base.children = []

        client = config.runtime_data.client
        camera_id = self._get_camera_id_or_raise(config, device)

        if kind == "movies":
            resp = await client.async_get_movies(camera_id)
        else:
            resp = await client.async_get_images(camera_id)

        sub_dirs: set[str] = set()
        parts = parsed_path.parts
        media_list = resp.get(KEY_MEDIA_LIST, []) if resp else []

        def get_media_sort_key(media: dict) -> str:
            """Get media sort key."""
            return media.get(KEY_PATH, "")

        for media in sorted(media_list, key=get_media_sort_key):
            if (
                KEY_PATH not in media
                or KEY_MIME_TYPE not in media
                or media[KEY_MIME_TYPE] not in MIME_TYPE_MAP.values()
            ):
                continue

            # Example path: '/2021-04-21/21-13-10.mp4'
            parts_media = PurePath(media[KEY_PATH]).parts

            if parts_media[: len(parts)] == parts and len(parts_media) > len(parts):
                full_child_path = str(PurePath(*parts_media[: len(parts) + 1]))
                display_child_path = parts_media[len(parts)]

                # Child is a media file.
                if len(parts) + 1 == len(parts_media):
                    if kind == "movies":
                        thumbnail_url = client.get_movie_url(
                            camera_id, full_child_path, preview=True
                        )
                    else:
                        thumbnail_url = client.get_image_url(
                            camera_id, full_child_path, preview=True
                        )

                    base.children.append(
                        BrowseMediaSource(
                            domain=DOMAIN,
                            identifier=f"{config.entry_id}#{device.id}#{kind}#{full_child_path}",
                            media_class=MEDIA_CLASS_MAP[kind],
                            media_content_type=media[KEY_MIME_TYPE],
                            title=display_child_path,
                            can_play=(kind == "movies"),
                            can_expand=False,
                            thumbnail=thumbnail_url,
                        )
                    )

                # Child is a subdirectory.
                elif len(parts) + 1 < len(parts_media):
                    if full_child_path not in sub_dirs:
                        sub_dirs.add(full_child_path)
                        base.children.append(
                            BrowseMediaSource(
                                domain=DOMAIN,
                                identifier=(
                                    f"{config.entry_id}#{device.id}"
                                    f"#{kind}#{full_child_path}"
                                ),
                                media_class=MediaClass.DIRECTORY,
                                media_content_type=(
                                    MediaType.VIDEO
                                    if kind == "movies"
                                    else MediaType.IMAGE
                                ),
                                title=display_child_path,
                                can_play=False,
                                can_expand=True,
                                children_media_class=MediaClass.DIRECTORY,
                            )
                        )
        return base