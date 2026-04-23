async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return media for the specified level of the directory tree.

        The top level is the root that contains devices. Inside each device are
        media for events for that device.
        """
        media_id: MediaId | None = parse_media_id(item.identifier)
        _LOGGER.debug(
            "Browsing media for identifier=%s, media_id=%s", item.identifier, media_id
        )
        devices = async_get_media_source_devices(self.hass)
        if media_id is None:
            # Browse the root and return child devices
            browse_root = _browse_root()
            browse_root.children = []
            for device_id, child_device in devices.items():
                browse_device = _browse_device(MediaId(device_id), child_device)
                if last_event_id := await _async_get_recent_event_id(
                    MediaId(device_id), child_device
                ):
                    browse_device.thumbnail = EVENT_THUMBNAIL_URL_FORMAT.format(
                        device_id=last_event_id.device_id,
                        event_token=last_event_id.event_token,
                    )
                    browse_device.can_play = True
                browse_root.children.append(browse_device)
            return browse_root

        # Browse either a device or events within a device
        if not (device := devices.get(media_id.device_id)):
            raise BrowseError(
                f"Unable to find device with identiifer: {item.identifier}"
            )
        # Clip previews are a session with multiple possible event types (e.g.
        # person, motion, etc) and a single mp4
        if CameraClipPreviewTrait.NAME in device.traits:
            clips: dict[
                str, ClipPreviewSession
            ] = await _async_get_clip_preview_sessions(device)
            if media_id.event_token is None:
                # Browse a specific device and return child events
                browse_device = _browse_device(media_id, device)
                browse_device.children = []
                for clip in clips.values():
                    event_id = MediaId(media_id.device_id, clip.event_token)
                    browse_device.children.append(
                        _browse_clip_preview(event_id, device, clip)
                    )
                return browse_device

            # Browse a specific event
            if not (single_clip := clips.get(media_id.event_token)):
                raise BrowseError(
                    f"Unable to find event with identiifer: {item.identifier}"
                )
            return _browse_clip_preview(media_id, device, single_clip)

        # Image events are 1:1 of media to event
        images: dict[str, ImageSession] = await _async_get_image_sessions(device)
        if media_id.event_token is None:
            # Browse a specific device and return child events
            browse_device = _browse_device(media_id, device)
            browse_device.children = []
            for image in images.values():
                event_id = MediaId(media_id.device_id, image.event_token)
                browse_device.children.append(
                    _browse_image_event(event_id, device, image)
                )
            return browse_device

        # Browse a specific event
        if not (single_image := images.get(media_id.event_token)):
            raise BrowseError(
                f"Unable to find event with identiifer: {item.identifier}"
            )
        return _browse_image_event(media_id, device, single_image)