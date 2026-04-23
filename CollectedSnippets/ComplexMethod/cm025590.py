async def _async_long_polling(self, *_: Any) -> None:
        """Use ONVIF long polling to immediately receive events."""
        # This task will be cancelled once _async_stop_long_polling is called
        while True:
            if self._api.baichuan.events_active or self._webhook_reachable:
                # TCP push or ONVIF push working, stop long polling
                self._long_poll_task = None
                await self._async_stop_long_polling()
                return

            try:
                channels = await self._api.pull_point_request()
            except ReolinkError as ex:
                if not self._long_poll_error and self._api.subscribed(
                    SubType.long_poll
                ):
                    _LOGGER.error("Error while requesting ONVIF pull point: %s", ex)
                    await self._api.unsubscribe(sub_type=SubType.long_poll)
                self._long_poll_error = True
                await asyncio.sleep(LONG_POLL_ERROR_COOLDOWN)
                continue
            except Exception:
                _LOGGER.exception(
                    "Unexpected exception while requesting ONVIF pull point"
                )
                await self._api.unsubscribe(sub_type=SubType.long_poll)
                raise

            self._long_poll_error = False

            if not self._long_poll_received:
                self._long_poll_received = True
                ir.async_delete_issue(self._hass, DOMAIN, "webhook_url")

            self._signal_write_ha_state(channels)

            # Cooldown to prevent CPU over usage on camera freezes
            await asyncio.sleep(LONG_POLL_COOLDOWN)