def _get_data(self, key: str, func: Callable[[], Any]) -> None:
        if not self.subscriptions.get(key):
            return
        if key in self.inflight_gets:
            _LOGGER.debug("Skipping already in-flight get for %s", key)
            return
        self.inflight_gets.add(key)
        _LOGGER.debug("Getting %s for subscribers %s", key, self.subscriptions[key])
        try:
            self.data[key] = func()
        except ResponseErrorLoginRequiredException:
            if not self.config_entry.options.get(CONF_UNAUTHENTICATED_MODE):
                _LOGGER.debug("Trying to authorize again")
                if self.client.user.login(
                    self.config_entry.data.get(CONF_USERNAME, ""),
                    self.config_entry.data.get(CONF_PASSWORD, ""),
                ):
                    _LOGGER.debug(
                        "success, %s will be updated by a future periodic run",
                        key,
                    )
                else:
                    _LOGGER.debug("failed")
                return
            _LOGGER.warning(
                "%s requires authorization, excluding from future updates", key
            )
            self.subscriptions.pop(key)
        except (ResponseErrorException, ExpatError) as exc:
            # Take ResponseErrorNotSupportedException, ExpatError, and generic
            # ResponseErrorException with a few select codes to mean the endpoint is
            # not supported.
            if not isinstance(
                exc, (ResponseErrorNotSupportedException, ExpatError)
            ) and exc.code not in (-1, 100006):
                raise
            _LOGGER.warning(
                "%s apparently not supported by device, excluding from future updates",
                key,
            )
            self.subscriptions.pop(key)
        finally:
            self.inflight_gets.discard(key)
            _LOGGER.debug("%s=%s", key, self.data.get(key))