async def async_update(self) -> None:
        """Update state."""
        if self._viaggiatreno is None:
            session = async_get_clientsession(self.hass)
            self._viaggiatreno = Viaggiatreno(session)
        try:
            await self._viaggiatreno.query_if_useful(self._line)
            self._tstatus = self._viaggiatreno.get_line_status(self._line)
            if self._tstatus is None:
                _LOGGER.error(
                    "Received status for line %s: None. Check the train and station IDs",
                    self._line,
                )
                return
        except (TimeoutError, aiohttp.ClientError) as exc:
            _LOGGER.error("Cannot connect to ViaggiaTreno API endpoint: %s", exc)
            return
        except ValueError:
            _LOGGER.error("Received non-JSON data from ViaggiaTreno API endpoint")
            return
        if self._tstatus is not None:
            if self._tstatus.state == TrainState.CANCELLED:
                self._state = CANCELLED_STRING
                self._icon = "mdi:cancel"
            elif self._tstatus.state == TrainState.NOT_YET_DEPARTED:
                self._state = NOT_DEPARTED_STRING
            elif self._tstatus.state == TrainState.ARRIVED:
                self._state = ARRIVED_STRING
            elif self._tstatus.state in {
                TrainState.RUNNING,
                TrainState.PARTIALLY_CANCELLED,
            }:
                delay_minutes = self._tstatus.timetable.delay
                self._state = delay_minutes
                self._icon = ICON
            else:
                self._state = NO_INFORMATION_STRING
            # Update attributes
            for info in MONITORED_INFO:
                self._attributes[info] = self._viaggiatreno.json[self._line][info]