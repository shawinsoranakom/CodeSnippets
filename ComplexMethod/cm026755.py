def async_enable_local_sdk(self) -> None:
        """Enable the local SDK."""
        _LOGGER.debug("async_enable_local_sdk")
        setup_successful = True
        setup_webhook_ids = []

        # Don't enable local SDK if ssl is enabled
        if self.hass.config.api and self.hass.config.api.use_ssl:
            self._local_sdk_active = False
            return

        for user_agent_id in self.async_get_agent_users():
            if (webhook_id := self.get_local_webhook_id(user_agent_id)) is None:
                setup_successful = False
                break

            _LOGGER.debug(
                "Register webhook handler %s for agent user id %s",
                partial_redact(webhook_id),
                partial_redact(user_agent_id),
            )
            try:
                webhook.async_register(
                    self.hass,
                    DOMAIN,
                    "Local Support for " + user_agent_id,
                    webhook_id,
                    self._handle_local_webhook,
                    local_only=True,
                )
                setup_webhook_ids.append(webhook_id)
            except ValueError:
                _LOGGER.warning(
                    "Webhook handler %s for agent user id %s is already defined!",
                    partial_redact(webhook_id),
                    partial_redact(user_agent_id),
                )
                setup_successful = False
                break

        if not setup_successful:
            _LOGGER.warning(
                "Local fulfillment failed to setup, falling back to cloud fulfillment"
            )
            for setup_webhook_id in setup_webhook_ids:
                webhook.async_unregister(self.hass, setup_webhook_id)

        self._local_sdk_active = setup_successful