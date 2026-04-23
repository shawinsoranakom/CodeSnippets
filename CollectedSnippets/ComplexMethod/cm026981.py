async def async_step_start_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start Z-Wave JS add-on."""
        if self.hass.config.country is None and (
            not self._rf_region or self._rf_region == "Automatic"
        ):
            # If the country is not set, we need to check the RF region add-on config.
            addon_info = await self._async_get_addon_info()
            rf_region: str | None = addon_info.options.get(CONF_ADDON_RF_REGION)
            self._rf_region = rf_region
            if rf_region is None or rf_region == "Automatic":
                # If the RF region is not set, we need to ask the user to select it.
                return await self.async_step_rf_region()
        if config_updates := self._addon_config_updates:
            # If we have updates to the add-on config, set them before starting the add-on.
            self._addon_config_updates = {}
            await self._async_set_addon_config(config_updates)

        if not self.start_task:
            self.start_task = self.hass.async_create_task(self._async_start_addon())

        if not self.start_task.done():
            return self.async_show_progress(
                step_id="start_addon",
                progress_action="start_addon",
                progress_task=self.start_task,
            )

        try:
            await self.start_task
        except (CannotConnect, AddonError, AbortFlow) as err:
            _LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="start_failed")
        finally:
            self.start_task = None

        return self.async_show_progress_done(next_step_id="finish_addon_setup")