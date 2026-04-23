async def _async_prefs_updated(self, prefs: CloudPreferences) -> None:
        """Handle updated preferences."""
        _LOGGER.debug("_async_prefs_updated")
        if not self._cloud.is_logged_in:
            if self.is_reporting_state:
                self.async_disable_report_state()
            if self.is_local_sdk_active:
                self.async_disable_local_sdk()
            return

        if (
            self.enabled
            and GOOGLE_DOMAIN not in self.hass.config.components
            and self.hass.is_running
        ):
            await async_setup_component(self.hass, GOOGLE_DOMAIN, {})

        sync_entities = False

        if self.should_report_state != self.is_reporting_state:
            if self.should_report_state:
                self.async_enable_report_state()
            else:
                self.async_disable_report_state()

            # State reporting is reported as a property on entities.
            # So when we change it, we need to sync all entities.
            sync_entities = True

        if self.enabled and not self.is_local_sdk_active:
            self.async_enable_local_sdk()
            sync_entities = True
        elif not self.enabled and self.is_local_sdk_active:
            self.async_disable_local_sdk()
            sync_entities = True

        if sync_entities and self.hass.is_running:
            await self.async_sync_entities_all()