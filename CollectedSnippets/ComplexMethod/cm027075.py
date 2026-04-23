def _publish_new_entries(self) -> None:
        """Publish new entries to the event bus."""
        assert self._feed is not None
        new_entry_count = 0
        firstrun = False
        self._last_entry_timestamp = self._storage.get_timestamp(self._feed_id)
        if not self._last_entry_timestamp:
            firstrun = True
            # Set last entry timestamp as epoch time if not available
            self._last_entry_timestamp = dt_util.utc_from_timestamp(0).timetuple()
        # locally cache self._last_entry_timestamp so that entries published at identical times can be processed
        last_entry_timestamp = self._last_entry_timestamp
        for entry in self._feed.entries:
            if firstrun or (
                (
                    time_stamp := entry.get("updated_parsed")
                    or entry.get("published_parsed")
                )
                and time_stamp > last_entry_timestamp
            ):
                self._update_and_fire_entry(entry)
                new_entry_count += 1
            else:
                _LOGGER.debug("Already processed entry %s", entry.get("link"))
        if new_entry_count == 0:
            self._log_no_entries()
        else:
            _LOGGER.debug("%d entries published in feed %s", new_entry_count, self.url)