async def _write_ffmpeg_data(
        self,
        request: BaseRequest,
        writer: AbstractStreamWriter,
        proc: asyncio.subprocess.Process,
    ) -> None:
        assert proc.stdout is not None
        assert proc.stderr is not None

        stderr_lines: deque[str] = deque(maxlen=_MAX_STDERR_LINES)
        stderr_task = self.hass.async_create_background_task(
            self._collect_ffmpeg_stderr(proc, stderr_lines),
            "ESPHome media proxy dump stderr",
        )

        try:
            # Pull audio chunks from ffmpeg and pass them to the HTTP client
            while (
                self.hass.is_running
                and (request.transport is not None)
                and (not request.transport.is_closing())
                and (chunk := await proc.stdout.read(self.chunk_size))
            ):
                await self.write(chunk)
        except asyncio.CancelledError:
            _LOGGER.debug("ffmpeg transcoding cancelled")
            # Abort the transport, we don't wait for ESPHome to drain the write buffer;
            # it may need a very long time or never finish if the player is paused.
            if request.transport:
                request.transport.abort()
            raise  # don't log error
        except Exception:
            _LOGGER.exception("Unexpected error during ffmpeg conversion")
            raise
        finally:
            # Allow conversion info to be removed
            self.convert_info.is_finished = True

            # Ensure subprocess and stderr cleanup run even if this task
            # is cancelled (e.g., during shutdown)
            try:
                # Terminate hangs, so kill is used
                if proc.returncode is None:
                    proc.kill()

                # Wait for process to exit so returncode is set
                await asyncio.wait_for(proc.wait(), timeout=_PROC_WAIT_TIMEOUT)

                # Let stderr collector finish draining
                if not stderr_task.done():
                    try:
                        await asyncio.wait_for(
                            stderr_task, timeout=_STDERR_DRAIN_TIMEOUT
                        )
                    except TimeoutError:
                        stderr_task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await stderr_task
            except TimeoutError:
                _LOGGER.warning(
                    "Timed out waiting for ffmpeg process to exit for device %s",
                    self.device_id,
                )
                stderr_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await stderr_task
            except asyncio.CancelledError:
                # Kill the process if we were interrupted
                if proc.returncode is None:
                    proc.kill()
                stderr_task.cancel()
                raise

            if proc.returncode is not None and proc.returncode > 0:
                _LOGGER.error(
                    "FFmpeg conversion failed for device %s (return code %s):\n%s",
                    self.device_id,
                    proc.returncode,
                    "\n".join(
                        _SENSITIVE_QUERY_PARAMS.sub(r"\1=REDACTED", line)
                        for line in stderr_lines
                    ),
                )

            # Close connection by writing EOF unless already closing
            if request.transport and not request.transport.is_closing():
                with contextlib.suppress(ConnectionResetError, RuntimeError, OSError):
                    await writer.write_eof()