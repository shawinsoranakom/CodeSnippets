async def trigger_observe_callback(
        self,
        hass: HomeAssistant,
        device: Device,
        new_device_state: dict[str, Any] | None = None,
    ) -> None:
        """Trigger the observe callback."""
        observe_command = next(
            (
                command
                for command in self.sent_commands
                if command.path == device.path and command.observe
            ),
            None,
        )
        assert observe_command

        device_path = "/".join(str(v) for v in device.path)
        device_state = deepcopy(device.raw)

        # Create a default observed state based on the sent commands.
        for command in self.sent_commands:
            if (data := command.data) is None or command.path_str != device_path:
                continue
            device_state = modify_state(device_state, data)

        # Allow the test to override the default observed state.
        if new_device_state is not None:
            device_state = modify_state(device_state, new_device_state)

        observe_command.process_result(device_state)

        await hass.async_block_till_done()