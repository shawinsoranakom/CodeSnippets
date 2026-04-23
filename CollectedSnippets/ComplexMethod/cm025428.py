async def _get_device_state(
        self, commands: set[type[Command]]
    ) -> dict[type[Command], str]:
        """Get the current state of the device."""
        new_state: dict[type[Command], str] = {}
        deferred_commands: list[type[Command]] = []

        power = await self._update_command_state(cmd.Power, new_state)

        if power == cmd.Power.ON:
            signal = await self._update_command_state(cmd.Signal, new_state)
            await self._update_command_state(cmd.Input, new_state)
            await self._update_command_state(cmd.LightTime, new_state)

            if signal == cmd.Signal.SIGNAL:
                for command in commands:
                    if command.depends:
                        # Command has dependencies so defer until below
                        deferred_commands.append(command)
                    else:
                        await self._update_command_state(command, new_state)

                # Deferred commands should have had dependencies met above
                for command in deferred_commands:
                    depend_command, depend_values = next(iter(command.depends.items()))
                    value: str | None = None
                    if depend_command in new_state:
                        value = new_state[depend_command]
                    elif depend_command in self.state:
                        value = self.state[depend_command]
                    if value and value in depend_values:
                        await self._update_command_state(command, new_state)

        elif self.state.get(cmd.Signal) != cmd.Signal.NONE:
            new_state[cmd.Signal] = cmd.Signal.NONE

        return new_state