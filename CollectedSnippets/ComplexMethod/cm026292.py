async def _build_event(
        self,
        data: ProtectData,
        event: dict[str, Any] | Event,
        thumbnail_only: bool = False,
    ) -> BrowseMediaSource:
        """Build media source for an individual event."""

        if isinstance(event, Event):
            event_id = event.id
            event_type = event.type
            start = event.start
            end = event.end
        else:
            event_id = event["id"]
            event_type = EventType(event["type"])
            start = from_js_time(event["start"])
            end = from_js_time(event["end"])

        assert end is not None

        title = dt_util.as_local(start).strftime("%x %X")
        duration = end - start
        title += f" {_format_duration(duration)}"
        if event_type in EVENT_MAP[SimpleEventType.RING]:
            event_text = "Ring Event"
        elif event_type in EVENT_MAP[SimpleEventType.MOTION]:
            event_text = "Motion Event"
        elif event_type in EVENT_MAP[SimpleEventType.SMART]:
            event_text = f"Object Detection - {_get_object_name(event)}"
        elif event_type in EVENT_MAP[SimpleEventType.AUDIO]:
            event_text = f"Audio Detection - {_get_audio_name(event)}"
        title += f" {event_text}"

        nvr = data.api.bootstrap.nvr
        if thumbnail_only:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=f"{nvr.id}:eventthumb:{event_id}",
                media_class=MediaClass.IMAGE,
                media_content_type="image/jpeg",
                title=title,
                can_play=True,
                can_expand=False,
                thumbnail=async_generate_thumbnail_url(
                    event_id, nvr.id, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT
                ),
            )

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{nvr.id}:event:{event_id}",
            media_class=MediaClass.VIDEO,
            media_content_type="video/mp4",
            title=title,
            can_play=True,
            can_expand=False,
            thumbnail=async_generate_thumbnail_url(
                event_id, nvr.id, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT
            ),
        )