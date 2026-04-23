async def _adb_exception_catcher(
            self: _ADBDeviceT, *args: _P.args, **kwargs: _P.kwargs
        ) -> _R | None:
            """Call an ADB-related method and catch exceptions."""
            if not self.available and not override_available:
                return None

            try:
                return await func(self, *args, **kwargs)
            except LockNotAcquiredException:
                # If the ADB lock could not be acquired, skip this command
                _LOGGER.debug(
                    (
                        "ADB command %s not executed because the connection is"
                        " currently in use"
                    ),
                    func.__name__,
                )
                return None
            except self.exceptions as err:
                if self.available:
                    _LOGGER.error(
                        (
                            "Failed to execute an ADB command. ADB connection re-"
                            "establishing attempt in the next update. Error: %s"
                        ),
                        err,
                    )

                await self.aftv.adb_close()
                self._attr_available = False
                return None
            except ServiceValidationError:
                # Service validation error is thrown because raised by remote services
                raise
            except Exception as err:  # noqa: BLE001
                # An unforeseen exception occurred. Close the ADB connection so that
                # it doesn't happen over and over again.
                if self.available:
                    _LOGGER.error(
                        (
                            "Unexpected exception executing an ADB command. ADB connection"
                            " re-establishing attempt in the next update. Error: %s"
                        ),
                        err,
                    )

                await self.aftv.adb_close()
                self._attr_available = False
                return None