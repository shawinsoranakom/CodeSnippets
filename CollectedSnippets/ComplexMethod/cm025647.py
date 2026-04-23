def _build_item_response(
        self, source: str, camera_id: str, event_id: int | None = None
    ) -> BrowseMediaSource:
        if event_id and event_id in self.events[camera_id]:
            created = dt.datetime.fromtimestamp(
                self.events[camera_id][event_id]["event_time"]
            )
            thumbnail = self.events[camera_id][event_id].get("snapshot", {}).get("url")
            message = remove_html_tags(
                self.events[camera_id][event_id].get("message", "")
            )
            title = f"{created} - {message}"
        else:
            title = self.hass.data[DOMAIN][DATA_CAMERAS].get(camera_id, MANUFACTURER)
            thumbnail = None

        if event_id:
            path = f"{source}/{camera_id}/{event_id}"
        else:
            path = f"{source}/{camera_id}"

        media_class = MediaClass.DIRECTORY if event_id is None else MediaClass.VIDEO

        media = BrowseMediaSource(
            domain=DOMAIN,
            identifier=path,
            media_class=media_class,
            media_content_type=MediaType.VIDEO,
            title=title,
            can_play=bool(
                event_id and self.events[camera_id][event_id].get("media_url")
            ),
            can_expand=event_id is None,
            thumbnail=thumbnail,
        )

        if not media.can_play and not media.can_expand:
            _LOGGER.debug(
                "Camera %s with event %s without media url found", camera_id, event_id
            )
            raise IncompatibleMediaSource

        if not media.can_expand:
            return media

        media.children = []
        # Append first level children
        if not camera_id:
            for cid in self.events:
                child = self._build_item_response(source, cid)
                if child:
                    media.children.append(child)
        else:
            for eid in self.events[camera_id]:
                try:
                    child = self._build_item_response(source, camera_id, eid)
                except IncompatibleMediaSource:
                    continue
                if child:
                    media.children.append(child)

        return media