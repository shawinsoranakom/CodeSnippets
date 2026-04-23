async def register_webhook(
        self,
        _: Any,
    ) -> None:
        """Register webhooks at Withings."""
        async with self._register_lock:
            if self._webhooks_registered:
                return
            self._cancel_pending_retry()
            if cloud.async_active_subscription(self.hass):
                webhook_url = await _async_cloudhook_generate_url(self.hass, self.entry)
            else:
                webhook_url = webhook_generate_url(
                    self.hass, self.entry.data[CONF_WEBHOOK_ID]
                )
            url = URL(webhook_url)
            if url.scheme != "https":
                if not self._webhook_url_invalid:
                    LOGGER.warning(
                        "Webhook not registered - HTTPS is required. "
                        "See https://www.home-assistant.io/integrations/withings/#webhook-requirements"
                    )
                    self._webhook_url_invalid = True
                return
            if url.port != 443:
                if not self._webhook_url_invalid:
                    LOGGER.warning(
                        "Webhook not registered - port 443 is required. "
                        "See https://www.home-assistant.io/integrations/withings/#webhook-requirements"
                    )
                    self._webhook_url_invalid = True
                return

            if not self._ha_webhook_registered:
                webhook_name = "Withings"
                if self.entry.title != DEFAULT_TITLE:
                    webhook_name = f"{DEFAULT_TITLE} {self.entry.title}"

                webhook_register(
                    self.hass,
                    DOMAIN,
                    webhook_name,
                    self.entry.data[CONF_WEBHOOK_ID],
                    get_webhook_handler(self.withings_data),
                    allowed_methods=[METH_POST],
                )
                self._ha_webhook_registered = True
                LOGGER.debug("Registered Withings webhook at hass: %s", webhook_url)

            self._webhook_url = webhook_url
            self._subscribe_attempt = 0

        await self._async_subscribe_webhook()