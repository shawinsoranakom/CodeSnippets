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
            and event.type is EventType.NFC_CARD_SCANNED
        ):
            event_data = {
                ATTR_EVENT_ID: event.id,
                KEYRINGS_USER_FULL_NAME: "",
                KEYRINGS_ULP_ID: "",
                KEYRINGS_USER_STATUS: "",
                KEYRINGS_KEY_TYPE_ID_NFC: "",
            }

            if event.metadata and event.metadata.nfc and event.metadata.nfc.nfc_id:
                nfc_id = event.metadata.nfc.nfc_id
                event_data[KEYRINGS_KEY_TYPE_ID_NFC] = nfc_id
                keyring = self.data.api.bootstrap.keyrings.by_registry_id(nfc_id)
                if keyring and keyring.ulp_user:
                    _add_ulp_user_infos(
                        self.data.api.bootstrap, event_data, keyring.ulp_user
                    )

            self._trigger_event(EVENT_TYPE_NFC_SCANNED, event_data)
            self.async_write_ha_state()