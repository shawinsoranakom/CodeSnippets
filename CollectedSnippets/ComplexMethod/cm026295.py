async def _build_camera(
        self, data: ProtectData, camera_id: str, build_children: bool = False
    ) -> BrowseMediaSource:
        """Build media source for selectors for a UniFi Protect camera."""

        name = "All Cameras"
        is_doorbell = data.api.bootstrap.has_doorbell
        has_smart = data.api.bootstrap.has_smart_detections
        camera: Camera | None = None
        if camera_id != "all":
            camera = data.api.bootstrap.cameras.get(camera_id)
            if camera is None:
                raise BrowseError(f"Unknown Camera ID: {camera_id}")
            name = camera.name or camera.market_name or camera.type
            is_doorbell = camera.feature_flags.is_doorbell
            has_smart = camera.feature_flags.has_smart_detect

        thumbnail_url: str | None = None
        if camera is not None:
            thumbnail_url = await self._get_camera_thumbnail_url(camera)
        source = BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{data.api.bootstrap.nvr.id}:browse:{camera_id}",
            media_class=MediaClass.DIRECTORY,
            media_content_type=VIDEO_FORMAT,
            title=name,
            can_play=False,
            can_expand=True,
            thumbnail=thumbnail_url,
            children_media_class=MediaClass.VIDEO,
        )

        if not build_children:
            return source

        source.children = [
            await self._build_events_type(data, camera_id, SimpleEventType.MOTION),
        ]

        if is_doorbell:
            source.children.insert(
                0,
                await self._build_events_type(data, camera_id, SimpleEventType.RING),
            )

        if has_smart:
            source.children.append(
                await self._build_events_type(data, camera_id, SimpleEventType.SMART)
            )
            source.children.append(
                await self._build_events_type(data, camera_id, SimpleEventType.AUDIO)
            )

        if is_doorbell or has_smart:
            source.children.insert(
                0,
                await self._build_events_type(data, camera_id, SimpleEventType.ALL),
            )

        source.title = self._breadcrumb(data, name)

        return source