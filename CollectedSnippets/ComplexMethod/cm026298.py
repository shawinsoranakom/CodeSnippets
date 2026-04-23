def _async_update_device_from_protect(self, device: ProtectDeviceType) -> None:
        description = self.entity_description

        super()._async_update_device_from_protect(device)
        if event := description.get_event_obj(device):
            self._event = event
            self._event_end = event.end if event else None

        # Process vehicle detection events with thumbnails
        if (
            event
            and event.type is EventType.SMART_DETECT
            and (thumbnails := self._get_vehicle_thumbnails(event))
        ):
            # Skip if same event with same data (no changes)
            if (
                self._fired_event_id == event.id
                and self._fired_event_data
                == self._build_event_data(event.id, thumbnails)
            ):
                return

            # New event arrived while timer pending for different event?
            # Fire the old event immediately since it has completed
            if self._latest_event_id and self._latest_event_id != event.id:
                # Only fire if we haven't already (shouldn't happen, but defensive)
                self._fire_vehicle_event(self._latest_event_id, self._latest_thumbnails)
                self._cancel_thumbnail_timer()

            # Store event data and extend/start the timer
            # Timer extension allows better thumbnails (with LPR) to arrive
            self._latest_event_id = event.id
            self._latest_thumbnails = thumbnails
            self._thumbnail_timer_due = (
                self.hass.loop.time() + VEHICLE_EVENT_DELAY_SECONDS
            )
            # Only schedule if no timer running; existing timer will re-arm
            if self._thumbnail_timer_cancel is None:
                self._async_set_thumbnail_timer()