async def async_send_command(
        self,
        commands: Iterable[str],
        device: str,
        num_repeats: int,
        delay_secs: float,
        hold_secs: float,
    ) -> None:
        """Send a list of commands to one device."""
        device_id = None
        if device.isdigit():
            _LOGGER.debug("%s: Device %s is numeric", self.name, device)
            if self._client.get_device_name(int(device)):
                device_id = device

        if device_id is None:
            _LOGGER.debug(
                "%s: Find device ID %s based on device name", self.name, device
            )
            device_id = self._client.get_device_id(str(device).strip())

        if device_id is None:
            _LOGGER.error("%s: Device %s is invalid", self.name, device)
            return

        _LOGGER.debug(
            (
                "Sending commands to device %s holding for %s seconds "
                "with a delay of %s seconds"
            ),
            device,
            hold_secs,
            delay_secs,
        )

        # Creating list of commands to send.
        snd_cmnd_list = []
        for _ in range(num_repeats):
            for single_command in commands:
                send_command = SendCommandDevice(
                    device=device_id, command=single_command, delay=hold_secs
                )
                snd_cmnd_list.append(send_command)
                if delay_secs > 0:
                    snd_cmnd_list.append(float(delay_secs))

        _LOGGER.debug("%s: Sending commands", self.name)
        try:
            result_list = await self._client.send_commands(snd_cmnd_list)
        except aioexc.TimeOut:
            _LOGGER.error("%s: Sending commands timed-out", self.name)
            return

        for result in result_list:
            _LOGGER.error(
                "Sending command %s to device %s failed with code %s: %s",
                result.command.command,
                result.command.device,
                result.code,
                result.msg,
            )