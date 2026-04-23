async def _async_subscribe_webhook(self, _: Any = None) -> None:
        """Attempt to subscribe to Withings webhooks."""

        async with self._register_lock:
            if self._webhooks_registered or self._webhook_url is None:
                return

            try:
                await async_subscribe_webhooks(
                    self.withings_data.client, self._webhook_url
                )
            except (
                WithingsUnauthorizedError,
                WithingsAuthenticationFailedError,
            ) as err:
                LOGGER.error(
                    "Authentication failed while subscribing to webhooks: %s",
                    err,
                )
                self.entry.async_start_reauth(self.hass)
                return
            except WithingsInvalidParamsError as err:
                LOGGER.error(
                    "Webhook URL rejected by Withings: %s",
                    err,
                )
                return
            except WithingsTooManyRequestsError as err:
                delay = min(
                    300 * (self._subscribe_attempt + 1), MAX_WEBHOOK_RETRY_INTERVAL
                )
                LOGGER.warning(
                    "Rate limited by Withings API (attempt %d): %s. "
                    "Retrying in %d seconds",
                    self._subscribe_attempt + 1,
                    err,
                    delay,
                )
            except WithingsError as err:
                base_delay = 30
                delay = min(
                    base_delay * (2**self._subscribe_attempt),
                    MAX_WEBHOOK_RETRY_INTERVAL,
                )
                LOGGER.warning(
                    "Failed to subscribe to Withings webhooks "
                    "(attempt %d): %s. Retrying in %d seconds",
                    self._subscribe_attempt + 1,
                    err,
                    delay,
                )
            else:
                for coordinator in self.withings_data.coordinators:
                    coordinator.webhook_subscription_listener(True)
                LOGGER.debug(
                    "Registered Withings webhook at Withings: %s", self._webhook_url
                )
                self.entry.async_on_unload(
                    self.hass.bus.async_listen_once(
                        EVENT_HOMEASSISTANT_STOP, self.unregister_webhook
                    )
                )
                self._webhooks_registered = True
                return

            self._subscribe_attempt += 1
            self._schedule_retry(delay)