async def _async_wrap(
        self: _YeelightBaseLightT, *args: _P.args, **kwargs: _P.kwargs
    ) -> _R | None:
        for attempts in range(2):
            try:
                _LOGGER.debug("Calling %s with %s %s", func, args, kwargs)
                return await func(self, *args, **kwargs)
            except TimeoutError as ex:
                # The wifi likely dropped, so we want to retry once since
                # python-yeelight will auto reconnect
                if attempts == 0:
                    continue
                raise HomeAssistantError(
                    f"Timed out when calling {func.__name__} for bulb "
                    f"{self.device.name} at {self.device.host}: {str(ex) or type(ex)}"
                ) from ex
            except OSError as ex:
                # A network error happened, the bulb is likely offline now
                self.device.async_mark_unavailable()
                self.async_state_changed()
                raise HomeAssistantError(
                    f"Error when calling {func.__name__} for bulb "
                    f"{self.device.name} at {self.device.host}: {str(ex) or type(ex)}"
                ) from ex
            except BulbException as ex:
                # The bulb likely responded but had an error
                raise HomeAssistantError(
                    f"Error when calling {func.__name__} for bulb "
                    f"{self.device.name} at {self.device.host}: {str(ex) or type(ex)}"
                ) from ex
        return None