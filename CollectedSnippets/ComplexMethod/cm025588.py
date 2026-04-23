async def _async_start_long_polling(self, initial: bool = False) -> None:
        """Start ONVIF long polling task."""
        if self._long_poll_task is None:
            try:
                await self._api.subscribe(sub_type=SubType.long_poll)
            except NotSupportedError as err:
                if initial:
                    raise
                # make sure the long_poll_task is always created to try again later
                if not self._lost_subscription_start:
                    self._lost_subscription_start = True
                    _LOGGER.error(
                        "Reolink %s event long polling subscription lost: %s",
                        self._api.nvr_name,
                        err,
                    )
            except ReolinkError as err:
                # make sure the long_poll_task is always created to try again later
                if not self._lost_subscription_start:
                    self._lost_subscription_start = True
                    _LOGGER.error(
                        "Reolink %s event long polling subscription lost: %s",
                        self._api.nvr_name,
                        err,
                    )
            else:
                self._lost_subscription_start = False
            self._long_poll_task = asyncio.create_task(self._async_long_polling())