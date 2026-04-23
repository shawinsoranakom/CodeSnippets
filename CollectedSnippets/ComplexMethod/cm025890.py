async def wrapper(
        self: _DenonDeviceT, *args: _P.args, **kwargs: _P.kwargs
    ) -> _R | None:
        available = True
        try:
            return await func(self, *args, **kwargs)
        except AvrTimoutError:
            available = False
            if self.available:
                _LOGGER.warning(
                    (
                        "Timeout connecting to Denon AVR receiver at host %s. "
                        "Device is unavailable"
                    ),
                    self._receiver.host,
                )
                self._attr_available = False
        except AvrNetworkError:
            available = False
            if self.available:
                _LOGGER.warning(
                    (
                        "Network error connecting to Denon AVR receiver at host %s. "
                        "Device is unavailable"
                    ),
                    self._receiver.host,
                )
                self._attr_available = False
        except AvrProcessingError:
            available = True
            if self.available:
                _LOGGER.warning(
                    (
                        "Update of Denon AVR receiver at host %s not complete. "
                        "Device is still available"
                    ),
                    self._receiver.host,
                )
        except AvrForbiddenError:
            available = False
            if self.available:
                _LOGGER.warning(
                    (
                        "Denon AVR receiver at host %s responded with HTTP 403 error. "
                        "Device is unavailable. Please consider power cycling your "
                        "receiver"
                    ),
                    self._receiver.host,
                )
                self._attr_available = False
        except AvrCommandError as err:
            available = False
            _LOGGER.error(
                "Command %s failed with error: %s",
                func.__name__,
                err,
            )
        except DenonAvrError:
            available = False
            _LOGGER.exception(
                "Error occurred in method %s for Denon AVR receiver", func.__name__
            )
        finally:
            if available and not self.available:
                _LOGGER.warning(
                    "Denon AVR receiver at host %s is available again",
                    self._receiver.host,
                )
                self._attr_available = True
        return None