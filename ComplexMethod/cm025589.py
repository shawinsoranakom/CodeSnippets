async def renew(self) -> None:
        """Renew the subscription of motion events (lease time is 15 minutes)."""
        await self._api.baichuan.check_subscribe_events()

        if self._api.baichuan.events_active and self._api.subscribed(SubType.push):
            # TCP push active, unsubscribe from ONVIF push because not needed
            self.unregister_webhook()
            await self._api.unsubscribe()

        if self._api.baichuan.privacy_mode():
            return  # API is shutdown, no need to subscribe

        try:
            if (
                self._onvif_push_supported
                and not self._api.baichuan.events_active
                and self._cancel_tcp_push_check is None
            ):
                await self._renew(SubType.push)

            if self._onvif_long_poll_supported and self._long_poll_task is not None:
                if not self._api.subscribed(SubType.long_poll):
                    _LOGGER.debug("restarting long polling task")
                    # To prevent 5 minute request timeout
                    await self._async_stop_long_polling()
                    await self._async_start_long_polling()
                else:
                    await self._renew(SubType.long_poll)
        except SubscriptionError as err:
            if not self._lost_subscription:
                self._lost_subscription = True
                _LOGGER.error(
                    "Reolink %s event subscription lost: %s",
                    self._api.nvr_name,
                    err,
                )
        else:
            self._lost_subscription = False