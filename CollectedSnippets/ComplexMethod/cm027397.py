async def _async_send_remote_message_target(self, target, registration, data):
        """Send a message to a target."""
        app_data = registration[ATTR_APP_DATA]
        push_token = app_data[ATTR_PUSH_TOKEN]
        push_url = app_data[ATTR_PUSH_URL]

        target_data = dict(data)
        target_data[ATTR_PUSH_TOKEN] = push_token

        reg_info = {
            ATTR_APP_ID: registration[ATTR_APP_ID],
            ATTR_APP_VERSION: registration[ATTR_APP_VERSION],
            ATTR_WEBHOOK_ID: target,
        }
        if ATTR_OS_VERSION in registration:
            reg_info[ATTR_OS_VERSION] = registration[ATTR_OS_VERSION]

        target_data["registration_info"] = reg_info

        try:
            async with asyncio.timeout(10):
                response = await async_get_clientsession(self.hass).post(
                    push_url, json=target_data
                )
                result = await response.json()

            if response.status in (
                HTTPStatus.OK,
                HTTPStatus.CREATED,
                HTTPStatus.ACCEPTED,
            ):
                log_rate_limits(self.hass, registration[ATTR_DEVICE_NAME], result)
                return

            fallback_error = result.get("errorMessage", "Unknown error")
            fallback_message = (
                f"Internal server error, please try again later: {fallback_error}"
            )
            message = result.get("message", fallback_message)

            if "message" in result:
                if message[-1] not in [".", "?", "!"]:
                    message += "."
                message += " This message is generated externally to Home Assistant."

            if response.status == HTTPStatus.TOO_MANY_REQUESTS:
                _LOGGER.warning(message)
                log_rate_limits(
                    self.hass, registration[ATTR_DEVICE_NAME], result, logging.WARNING
                )
            else:
                _LOGGER.error(message)

        except TimeoutError:
            _LOGGER.error("Timeout sending notification to %s", push_url)
        except aiohttp.ClientError as err:
            _LOGGER.error("Error sending notification to %s: %r", push_url, err)