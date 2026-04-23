async def _async_update_data(self) -> dict[str, Any]:
        """Update state with the current value of a command."""
        commands: set[type[Command]] = set(self.async_contexts())
        commands = commands.difference(CORE_COMMANDS)

        last_timeout: JvcProjectorTimeoutError | None = None

        for _ in range(TIMEOUT_RETRIES):
            try:
                new_state = await self._get_device_state(commands)
                break
            except JvcProjectorTimeoutError as err:
                # Timeouts are expected when the projector loses signal and ignores commands for a brief time.
                last_timeout = err
                await asyncio.sleep(TIMEOUT_SLEEP)
        else:
            raise UpdateFailed(str(last_timeout)) from last_timeout

        # Clear state on signal loss
        if (
            new_state.get(cmd.Signal) == cmd.Signal.NONE
            and self.state.get(cmd.Signal) != cmd.Signal.NONE
        ):
            self.state = {k: v for k, v in self.state.items() if k in CORE_COMMANDS}

        # Update state with new values
        for k, v in new_state.items():
            self.state[k] = v

        if self.state[cmd.Power] != cmd.Power.STANDBY:
            self.update_interval = INTERVAL_FAST
        else:
            self.update_interval = INTERVAL_SLOW

        return {k.name: v for k, v in self.state.items()}