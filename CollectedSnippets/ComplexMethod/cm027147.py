async def _connect_and_loop(self) -> None:
        """Connect to satellite and run pipelines until an error occurs."""
        while self.is_running and (not self.device.is_muted):
            try:
                await self._connect()
                break
            except ConnectionError:
                self._client = None  # client is not valid

                await self.on_reconnect()

        if self._client is None:
            return

        _LOGGER.debug("Connected to satellite")

        if (not self.is_running) or self.device.is_muted:
            # Run was cancelled or satellite was disabled during connection
            return

        # Tell satellite that we're ready
        await self._client.write_event(RunSatellite().event())

        # Run until stopped or muted
        while self.is_running and (not self.device.is_muted):
            await self._run_pipeline_loop()