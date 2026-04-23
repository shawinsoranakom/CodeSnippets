async def _watchdog(self) -> None:
        """Keep respawning go2rtc servers.

        A new go2rtc server is spawned if the process terminates or the API
        stops responding.
        """
        while True:
            try:
                monitor_process_task = asyncio.create_task(self._monitor_process())
                self._watchdog_tasks.append(monitor_process_task)
                monitor_process_task.add_done_callback(self._watchdog_tasks.remove)
                monitor_api_task = asyncio.create_task(self._monitor_api())
                self._watchdog_tasks.append(monitor_api_task)
                monitor_api_task.add_done_callback(self._watchdog_tasks.remove)
                try:
                    await asyncio.gather(monitor_process_task, monitor_api_task)
                except Go2RTCWatchdogError:
                    _LOGGER.debug("Caught Go2RTCWatchdogError")
                    for task in self._watchdog_tasks:
                        if task.done():
                            if not task.cancelled():
                                task.exception()
                            continue
                        task.cancel()
                    await asyncio.sleep(_RESPAWN_COOLDOWN)
                    try:
                        await self._stop()
                        _LOGGER.warning("Go2rtc unexpectedly stopped, server log:")
                        self._log_server_output(logging.WARNING)
                        _LOGGER.debug("Spawning new go2rtc server")
                        with suppress(Go2RTCServerStartError):
                            await self._start()
                    except Exception:
                        _LOGGER.exception(
                            "Unexpected error when restarting go2rtc server"
                        )
            except Exception:
                _LOGGER.exception("Unexpected error in go2rtc server watchdog")