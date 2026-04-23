async def _async_poll_all_motion(self, *_: Any) -> None:
        """Poll motion and AI states until the first ONVIF push is received."""
        if (
            self._api.baichuan.events_active
            or self._webhook_reachable
            or self._long_poll_received
        ):
            # TCP push, ONVIF push or long polling is working, stop fast polling
            self._cancel_poll = None
            return

        try:
            if self._api.session_active:
                await self._api.get_motion_state_all_ch()
        except ReolinkError as err:
            if not self._fast_poll_error:
                _LOGGER.error(
                    "Reolink error while polling motion state for host %s:%s: %s",
                    self._api.host,
                    self._api.port,
                    err,
                )
            self._fast_poll_error = True
        else:
            if self._api.session_active:
                self._fast_poll_error = False
        finally:
            # schedule next poll
            if not self._hass.is_stopping:
                self._cancel_poll = async_call_later(
                    self._hass, POLL_INTERVAL_NO_PUSH, self._poll_job
                )

        self._signal_write_ha_state()