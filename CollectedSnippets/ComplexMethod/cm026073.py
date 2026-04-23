async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a command to one device."""
        num_repeats = kwargs[ATTR_NUM_REPEATS]
        delay = kwargs.get(ATTR_DELAY_SECS, DEFAULT_DELAY_SECS)
        hold_secs = kwargs.get(ATTR_HOLD_SECS, DEFAULT_HOLD_SECS)

        if not self.atv:
            _LOGGER.error("Unable to send commands, not connected to %s", self.name)
            return

        for _ in range(num_repeats):
            for single_command in command:
                attr_value: Any = None
                if attributes := COMMAND_TO_ATTRIBUTE.get(single_command):
                    attr_value = self.atv
                    for attr_name in attributes:
                        attr_value = getattr(attr_value, attr_name, None)
                if not attr_value:
                    attr_value = getattr(self.atv.remote_control, single_command, None)
                if not attr_value:
                    raise ValueError("Command not found. Exiting sequence")

                _LOGGER.debug("Sending command %s", single_command)

                if hold_secs >= 1:
                    await attr_value(action=InputAction.Hold)
                else:
                    await attr_value()

                await asyncio.sleep(delay)