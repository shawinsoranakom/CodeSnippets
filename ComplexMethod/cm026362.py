async def _async_handle_command(self, command, *args):
        """Do bookkeeping for command, send it to rflink and update state."""
        self.cancel_queued_send_commands()

        if command == "turn_on":
            cmd = "on"
            self._state = True

        elif command == "turn_off":
            cmd = "off"
            self._state = False

        elif command == "dim":
            # convert brightness to rflink dim level
            cmd = str(brightness_to_rflink(args[0]))
            self._state = True

        elif command == "toggle":
            cmd = "on"
            # if the state is unknown or false, it gets set as true
            # if the state is true, it gets set as false
            self._state = self._state in [None, False]

        # Cover options for RFlink
        elif command == "close_cover":
            cmd = "DOWN"
            self._state = False

        elif command == "open_cover":
            cmd = "UP"
            self._state = True

        elif command == "stop_cover":
            cmd = "STOP"
            self._state = True

        # Send initial command and queue repetitions.
        # This allows the entity state to be updated quickly and not having to
        # wait for all repetitions to be sent
        await self._async_send_command(cmd, self._signal_repetitions)

        # Update state of entity
        self.async_write_ha_state()