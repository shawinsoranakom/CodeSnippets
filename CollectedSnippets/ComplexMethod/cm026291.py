async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return a browsable UniFi Protect media source.

        Identifier formatters for UniFi Protect media sources are all in IDs from
        the UniFi Protect instance since events may not always map 1:1 to a Home
        Assistant device or entity. It also drasically speeds up resolution.

        The UniFi Protect Media source is timebased for the events recorded by the NVR.
        So its structure is a bit different then many other media players. All browsable
        media is a video clip. The media source could be greatly cleaned up if/when the
        frontend has filtering supporting.

        * ... Each NVR Console (hidden if there is only one)
            * All Cameras
            * ... Camera X
                * All Events
                * ... Event Type X
                    * Last 24 Hours -> Events
                    * Last 7 Days -> Events
                    * Last 30 Days -> Events
                    * ... This Month - X
                        * Whole Month -> Events
                        * ... Day X -> Events

        Accepted identifier formats:

        * {nvr_id}:event:{event_id}
            Specific Event for NVR
        * {nvr_id}:eventthumb:{event_id}
            Specific Event Thumbnail for NVR
        * {nvr_id}:browse
            Root NVR browse source
        * {nvr_id}:browse:all|{camera_id}
            Root Camera(s) browse source
        * {nvr_id}:browse:all|{camera_id}:all|{event_type}
            Root Camera(s) Event Type(s) browse source
        * {nvr_id}:browse:all|{camera_id}:all|{event_type}:recent:{day_count}
            Listing of all events in last {day_count}, sorted in reverse chronological order
        * {nvr_id}:browse:all|{camera_id}:all|{event_type}:range:{year}:{month}
            List of folders for each day in month + all events for month
        * {nvr_id}:browse:all|{camera_id}:all|{event_type}:range:{year}:{month}:all|{day}
            Listing of all events for give {day} + {month} + {year} combination in chronological order
        """

        if not item.identifier:
            return await self._build_sources()

        parts = item.identifier.split(":")

        try:
            data = self.data_sources[parts[0]]
        except (KeyError, IndexError) as err:
            _bad_identifier(item.identifier, err)

        if len(parts) < 2:
            _bad_identifier(item.identifier)

        try:
            identifier_type = IdentifierType(parts[1])
        except ValueError as err:
            _bad_identifier(item.identifier, err)

        if identifier_type in (IdentifierType.EVENT, IdentifierType.EVENT_THUMB):
            thumbnail_only = identifier_type == IdentifierType.EVENT_THUMB
            return await self._resolve_event(data, parts[2], thumbnail_only)

        # rest are params for browse
        parts = parts[2:]

        # {nvr_id}:browse
        if len(parts) == 0:
            return await self._build_console(data)

        # {nvr_id}:browse:all|{camera_id}
        camera_id = parts.pop(0)
        if len(parts) == 0:
            return await self._build_camera(data, camera_id, build_children=True)

        # {nvr_id}:browse:all|{camera_id}:all|{event_type}
        try:
            event_type = SimpleEventType(parts.pop(0).lower())
        except (IndexError, ValueError) as err:
            _bad_identifier(item.identifier, err)

        if len(parts) == 0:
            return await self._build_events_type(
                data, camera_id, event_type, build_children=True
            )

        try:
            time_type = IdentifierTimeType(parts.pop(0))
        except ValueError as err:
            _bad_identifier(item.identifier, err)

        if len(parts) == 0:
            _bad_identifier(item.identifier)

        # {nvr_id}:browse:all|{camera_id}:all|{event_type}:recent:{day_count}
        if time_type == IdentifierTimeType.RECENT:
            try:
                days = int(parts.pop(0))
            except (IndexError, ValueError) as err:
                _bad_identifier(item.identifier, err)

            return await self._build_recent(
                data, camera_id, event_type, days, build_children=True
            )

        # {nvr_id}:all|{camera_id}:all|{event_type}:range:{year}:{month}
        # {nvr_id}:all|{camera_id}:all|{event_type}:range:{year}:{month}:all|{day}
        try:
            start, is_month, is_all = self._parse_range(parts)
        except (IndexError, ValueError) as err:
            _bad_identifier(item.identifier, err)

        if is_month:
            return await self._build_month(
                data, camera_id, event_type, start, build_children=True
            )
        return await self._build_days(
            data, camera_id, event_type, start, build_children=True, is_all=is_all
        )