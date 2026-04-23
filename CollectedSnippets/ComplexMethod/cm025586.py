async def _async_check_tcp_push(self, *_: Any) -> None:
        """Check the TCP push subscription."""
        if self._api.baichuan.events_active:
            ir.async_delete_issue(self._hass, DOMAIN, "webhook_url")
            self._cancel_tcp_push_check = None
            return

        _LOGGER.debug(
            "Reolink %s, did not receive initial TCP push event after %i seconds",
            self._api.nvr_name,
            FIRST_TCP_PUSH_TIMEOUT,
        )

        if self._onvif_push_supported:
            try:
                await self.subscribe()
            except ReolinkError:
                self._onvif_push_supported = False
                self.unregister_webhook()
                await self._api.unsubscribe()
            else:
                if self._api.supported(None, "initial_ONVIF_state"):
                    _LOGGER.debug(
                        "Waiting for initial ONVIF state on webhook '%s'",
                        self._webhook_url,
                    )
                else:
                    _LOGGER.debug(
                        "Camera model %s most likely does not push its initial state"
                        " upon ONVIF subscription, do not check",
                        self._api.model,
                    )
                self._cancel_onvif_check = async_call_later(
                    self._hass, FIRST_ONVIF_TIMEOUT, self._async_check_onvif
                )

        # start long polling if ONVIF push failed immediately
        if not self._onvif_push_supported and not self._api.baichuan.privacy_mode():
            _LOGGER.debug(
                "Camera model %s does not support ONVIF push, using ONVIF long polling instead",
                self._api.model,
            )
            try:
                await self._async_start_long_polling(initial=True)
            except NotSupportedError:
                _LOGGER.debug(
                    "Camera model %s does not support ONVIF long polling, using fast polling instead",
                    self._api.model,
                )
                self._onvif_long_poll_supported = False
                await self._api.unsubscribe()
                await self._async_poll_all_motion()
            else:
                self._cancel_long_poll_check = async_call_later(
                    self._hass,
                    FIRST_ONVIF_LONG_POLL_TIMEOUT,
                    self._async_check_onvif_long_poll,
                )

        self._cancel_tcp_push_check = None