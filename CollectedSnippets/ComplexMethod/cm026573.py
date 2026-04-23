def send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message to the Lambda APNS gateway."""
        data: dict[str, Any] = {ATTR_MESSAGE: message}

        # Remove default title from notifications.
        if (
            kwargs.get(ATTR_TITLE) is not None
            and kwargs.get(ATTR_TITLE) != ATTR_TITLE_DEFAULT
        ):
            data[ATTR_TITLE] = kwargs.get(ATTR_TITLE)

        if not (targets := kwargs.get(ATTR_TARGET)):
            targets = enabled_push_ids(self.hass)

        if kwargs.get(ATTR_DATA) is not None:
            data[ATTR_DATA] = kwargs.get(ATTR_DATA)

        for target in targets:
            if target not in enabled_push_ids(self.hass):
                _LOGGER.error("The target (%s) does not exist in .ios.conf", targets)
                return

            data[ATTR_TARGET] = target

            req = requests.post(PUSH_URL, json=data, timeout=10)

            if req.status_code != HTTPStatus.CREATED:
                fallback_error = req.json().get("errorMessage", "Unknown error")
                fallback_message = (
                    f"Internal server error, please try again later: {fallback_error}"
                )
                message = req.json().get("message", fallback_message)
                if req.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                    _LOGGER.warning(message)
                    log_rate_limits(self.hass, target, req.json(), 30)
                else:
                    _LOGGER.error(message)
            else:
                log_rate_limits(self.hass, target, req.json())