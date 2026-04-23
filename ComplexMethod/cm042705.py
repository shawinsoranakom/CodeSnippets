async def _start_request_processing(self) -> None:
        """Starts consuming Spider.start() output and sending scheduled
        requests."""
        # Starts the processing of scheduled requests, as well as a periodic
        # call to that processing method for scenarios where the scheduler
        # reports having pending requests but returns none.
        try:
            assert self._slot is not None  # typing
            self._slot.nextcall.schedule()
            self._slot.heartbeat.start(self._SLOT_HEARTBEAT_INTERVAL)

            while self._start and self.spider and self.running:
                await self._process_start_next()
                if not self.needs_backout():
                    # Give room for the outcome of self._process_start_next() to be
                    # processed before continuing with the next iteration.
                    self._slot.nextcall.schedule()
                    await self._slot.nextcall.wait()
        except (asyncio.exceptions.CancelledError, CancelledError):
            # self.stop_async() has cancelled us, nothing to do
            return
        except Exception:
            # an error happened, log it and stop the engine
            self._start_request_processing_awaitable = None
            logger.error(
                "Error while processing requests from start()",
                exc_info=True,
                extra={"spider": self.spider},
            )
            await self.stop_async()