def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if (data := self.coordinator.data) is None or not data:
            return

        # RSS feeds are normally sorted reverse chronologically by published date
        # so we always take the first entry in list, since we only care about the latest entry
        feed_data: FeedParserDict = data[0]

        if description := feed_data.get("description"):
            description = html.unescape(description)

        if title := feed_data.get("title"):
            title = html.unescape(title)

        if content := feed_data.get("content"):
            if isinstance(content, list) and isinstance(content[0], dict):
                content = content[0].get("value")
            content = html.unescape(content)

        self._trigger_event(
            EVENT_FEEDREADER,
            {
                ATTR_DESCRIPTION: description,
                ATTR_TITLE: title,
                ATTR_LINK: feed_data.get("link"),
                ATTR_CONTENT: content,
            },
        )
        self.async_write_ha_state()