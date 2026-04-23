async def _check_hangup(self) -> None:
        """Continuously checks if an audio chunk was received within a time limit.

        If not, the caller is presumed to have hung up and the call is ended.
        """
        try:
            while True:
                current_time = time.monotonic()
                if (self._last_chunk_time is not None) and (
                    (current_time - self._last_chunk_time) > _HANGUP_SEC
                ):
                    # Caller hung up
                    _LOGGER.debug("Hang up")
                    self._announcement = None
                    if self._run_pipeline_task is not None:
                        _LOGGER.debug("Cancelling running pipeline")
                        self._run_pipeline_task.cancel()
                    if not self._call_end_future.done():
                        self._call_end_future.set_result(None)
                    self.disconnect()
                    break

                await asyncio.sleep(_HANGUP_SEC / 2)
        except asyncio.CancelledError:
            # Don't swallow cancellation
            if (current_task := asyncio.current_task()) and current_task.cancelling():
                raise
            _LOGGER.debug("Check hangup cancelled")