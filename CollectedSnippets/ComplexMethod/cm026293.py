async def _build_events(
        self,
        data: ProtectData,
        start: datetime,
        end: datetime,
        camera_id: str | None = None,
        event_types: set[EventType] | None = None,
        reserve: bool = False,
    ) -> list[BrowseMediaSource]:
        """Build media source for a given range of time and event type."""

        event_types = event_types or EVENT_MAP[SimpleEventType.ALL]
        types = list(event_types)
        sources: list[BrowseMediaSource] = []
        events = await data.api.get_events_raw(
            start=start, end=end, types=types, limit=data.max_events
        )
        events = sorted(events, key=lambda e: cast(int, e["start"]), reverse=reserve)
        for event in events:
            # do not process ongoing events
            if event.get("start") is None or event.get("end") is None:
                continue

            if camera_id is not None and event.get("camera") != camera_id:
                continue

            # smart detect events have a paired motion event
            if event.get("type") == EventType.MOTION.value and event.get(
                "smartDetectEvents"
            ):
                continue

            sources.append(await self._build_event(data, event))

        return sources