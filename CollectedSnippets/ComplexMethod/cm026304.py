def _find_active_event_with_object_type(
        self, device: ProtectDeviceType
    ) -> Event | None:
        """Find an active event containing this sensor's object type.

        Fallback for issue #152133: last_smart_detect_event_ids may not update
        immediately when a new detection type is added to an ongoing event.
        """
        obj_type = self.entity_description.ufp_obj_type
        if obj_type is None or not isinstance(device, Camera):
            return None

        # Check known active event IDs from camera first (fast path)
        for event_id in device.last_smart_detect_event_ids.values():
            if (
                event_id
                and (event := self.data.api.bootstrap.events.get(event_id))
                and event.end is None
                and obj_type in event.smart_detect_types
            ):
                return event

        return None