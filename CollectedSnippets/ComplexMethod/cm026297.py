def _async_update_device_from_protect(self, device: ProtectDeviceType) -> None:
        description = self.entity_description

        prev_event = self._event
        prev_event_end = self._event_end
        super()._async_update_device_from_protect(device)
        if event := description.get_event_obj(device):
            self._event = event
            self._event_end = event.end if event else None

        if (
            event
            and not self._event_already_ended(prev_event, prev_event_end)
            and event.type is EventType.FINGERPRINT_IDENTIFIED
        ):
            event_data = {
                ATTR_EVENT_ID: event.id,
                KEYRINGS_USER_FULL_NAME: "",
                KEYRINGS_ULP_ID: "",
            }
            event_identified = EVENT_TYPE_FINGERPRINT_NOT_IDENTIFIED
            if (
                event.metadata
                and event.metadata.fingerprint
                and event.metadata.fingerprint.ulp_id
            ):
                event_identified = EVENT_TYPE_FINGERPRINT_IDENTIFIED
                ulp_id = event.metadata.fingerprint.ulp_id
                if ulp_id:
                    event_data[KEYRINGS_ULP_ID] = ulp_id
                    _add_ulp_user_infos(self.data.api.bootstrap, event_data, ulp_id)

            self._trigger_event(event_identified, event_data)
            self.async_write_ha_state()