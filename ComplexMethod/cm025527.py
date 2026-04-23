def _handle_device_registry_updated(
        self, event: Event[dr.EventDeviceRegistryUpdatedData]
    ) -> None:
        """Handle when device registry updated."""
        if (
            not self.enabled
            or not self._cloud.is_logged_in
            or self.hass.state is not CoreState.running
        ):
            return

        # Device registry is only used for area changes. All other changes are ignored.
        if event.data["action"] != "update" or "area_id" not in event.data["changes"]:
            return

        # Check if any exposed entity uses the device area
        if not any(
            entity_entry.area_id is None
            and self._should_expose_entity_id(entity_entry.entity_id)
            for entity_entry in er.async_entries_for_device(
                er.async_get(self.hass), event.data["device_id"]
            )
        ):
            return

        self.async_schedule_google_sync_all()