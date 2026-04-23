async def async_process_event(
        self, event: SonosEvent, speaker: SonosSpeaker
    ) -> None:
        """Process the event payload in an async lock and update entities."""
        event_id = event.variables["favorites_update_id"]
        container_ids = event.variables["container_update_i_ds"]
        if not container_ids or not (match := re.search(r"FV:2,(\d+)", container_ids)):
            return

        container_id = int(match.group(1))
        event_id = int(event_id.split(",")[-1])

        async with self.cache_update_lock:
            last_poll_id = self.last_polled_ids.get(speaker.uid)
            if (
                self.last_processed_event_id
                and event_id <= self.last_processed_event_id
            ):
                # Skip updates if this event_id has already been seen
                if not last_poll_id:
                    self.last_polled_ids[speaker.uid] = container_id
                return

            if last_poll_id and container_id <= last_poll_id:
                return

            speaker.event_stats.process(event)
            _LOGGER.debug(
                "New favorites event %s from %s (was %s)",
                event_id,
                speaker.soco,
                self.last_processed_event_id,
            )
            self.last_processed_event_id = event_id
            await self.async_update_entities(speaker.soco, container_id)