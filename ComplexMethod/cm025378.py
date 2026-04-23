def wrapper(self: _T, *args: _P.args, **kwargs: _P.kwargs) -> _R | None:
            """Wrap for all soco UPnP exception."""
            args_soco = next((arg for arg in args if isinstance(arg, SoCo)), None)
            try:
                result = funct(self, *args, **kwargs)
            except (OSError, SoCoException, SoCoUPnPException, Timeout) as err:
                error_code = getattr(err, "error_code", None)
                function = funct.__qualname__
                if errorcodes and error_code in errorcodes:
                    _LOGGER.debug(
                        "Error code %s ignored in call to %s", error_code, function
                    )
                    return None

                if (target := _find_target_identifier(self, args_soco)) is None:
                    raise RuntimeError("Unexpected use of soco_error") from err

                message = f"Error calling {function} on {target}: {err}"
                raise SonosUpdateError(message) from err

            dispatch_soco = args_soco or self.soco  # type: ignore[union-attr]
            dispatcher_send(
                self.hass,
                f"{SONOS_SPEAKER_ACTIVITY}-{dispatch_soco.uid}",
                funct.__qualname__,
            )
            return result