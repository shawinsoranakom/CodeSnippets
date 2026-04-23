def _async_update_device_from_protect(self, device: ProtectDeviceType) -> None:
        description = self.entity_description

        prev_event = self._event
        prev_event_end = self._event_end
        super()._async_update_device_from_protect(device)

        event = description.get_event_obj(device)
        if event is None:
            # Fallback for #152133: check active events directly
            event = self._find_active_event_with_object_type(device)

        if event:
            self._event = event
            self._event_end = event.end

        if not (
            event
            and (
                description.ufp_obj_type is None
                or description.has_matching_smart(event)
            )
            and not self._event_already_ended(prev_event, prev_event_end)
        ):
            self._set_event_done()
            return

        self._attr_is_on = True
        self._set_event_attrs(event)
        if event.end:
            self._async_event_with_immediate_end()