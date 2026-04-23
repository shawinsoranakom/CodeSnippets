async def async_update(self) -> None:
        """Update Electra device."""

        # if we communicated a change to the API in the last API_DELAY seconds,
        # then don't receive any updates as the API takes few seconds
        # until it start sending it last recent change
        if self._last_state_update and int(time.time()) < (
            self._last_state_update + API_DELAY
        ):
            _LOGGER.debug("Skipping state update, keeping old values")
            return

        self._last_state_update = 0

        try:
            # skip the first update only as we already got the devices with their current state
            if self._skip_update:
                self._skip_update = False
            else:
                await self._api.get_last_telemtry(self._electra_ac_device)

            if not self.available:
                # show the warning once upon state change
                if self._was_available:
                    _LOGGER.warning(
                        "Electra AC %s (%s) is not available, check its status in the Electra Smart mobile app",
                        self.name,
                        self._electra_ac_device.mac,
                    )
                    self._was_available = False
                return

            if not self._was_available:
                _LOGGER.debug(
                    "%s (%s) is now available",
                    self._electra_ac_device.mac,
                    self.name,
                )
                self._was_available = True

            _LOGGER.debug(
                "%s (%s) state updated: %s",
                self._electra_ac_device.mac,
                self.name,
                self._electra_ac_device.__dict__,
            )
        except ElectraApiError as exp:
            self._consecutive_failures += 1
            _LOGGER.warning(
                "Failed to get %s state: %s (try #%i since last success), keeping old state",
                self.name,
                exp,
                self._consecutive_failures,
            )

            if self._consecutive_failures >= CONSECUTIVE_FAILURE_THRESHOLD:
                raise HomeAssistantError(
                    f"Failed to get {self.name} state: {exp} for the {self._consecutive_failures} time",
                ) from ElectraApiError

        self._consecutive_failures = 0
        self._update_device_attrs()