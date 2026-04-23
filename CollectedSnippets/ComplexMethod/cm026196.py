def update(self) -> None:
        """Update the sensor."""

        LOGGER.debug("Running update on %s", self._service_name)
        try:
            # port connection, and last caller info
            if "Caller Info" in self._service_name or "Port" in self._service_name:
                services = self._pyobihai.get_line_state()

                if services is not None and self._service_name in services:
                    self._attr_native_value = services.get(self._service_name)
            elif self._service_name == "Call Direction":
                call_direction = self._pyobihai.get_call_direction()

                if self._service_name in call_direction:
                    self._attr_native_value = call_direction.get(self._service_name)
            else:  # SIP Profile service sensors, phone sensor, and last reboot
                services = self._pyobihai.get_state()

                if self._service_name in services:
                    self._attr_native_value = services.get(self._service_name)

            if not self.requester.available:
                self.requester.available = True
                LOGGER.warning("Connection restored")
            self._attr_available = True

        except RequestException as exc:
            if self.requester.available:
                LOGGER.warning("Connection failed, Obihai offline? %s", exc)
            self._attr_native_value = None
            self._attr_available = False
            self.requester.available = False
        except IndexError as exc:
            if self.requester.available:
                LOGGER.warning("Connection failed, bad response: %s", exc)
            self._attr_native_value = None
            self._attr_available = False
            self.requester.available = False