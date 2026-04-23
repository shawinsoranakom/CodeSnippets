async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to the Lambda APNS gateway."""
        data = {ATTR_MESSAGE: message}

        # Remove default title from notifications.
        if (
            title_arg := kwargs.get(ATTR_TITLE)
        ) is not None and title_arg != ATTR_TITLE_DEFAULT:
            data[ATTR_TITLE] = title_arg
        if not (targets := kwargs.get(ATTR_TARGET)):
            targets = push_registrations(self.hass).values()

        if (data_arg := kwargs.get(ATTR_DATA)) is not None:
            data[ATTR_DATA] = data_arg

        local_push_channels = self.hass.data[DOMAIN][DATA_PUSH_CHANNEL]

        failed_targets = []
        for target in targets:
            registration = self.hass.data[DOMAIN][DATA_CONFIG_ENTRIES][target].data

            if target in local_push_channels:
                local_push_channels[target].async_send_notification(
                    data,
                    partial(
                        self._async_send_remote_message_target, target, registration
                    ),
                )
                continue

            # Test if local push only.
            if ATTR_PUSH_URL not in registration[ATTR_APP_DATA]:
                failed_targets.append(target)
                continue

            await self._async_send_remote_message_target(target, registration, data)

        if failed_targets:
            raise HomeAssistantError(
                f"Device(s) with webhook id(s) {', '.join(failed_targets)} not connected to local push notifications"
            )