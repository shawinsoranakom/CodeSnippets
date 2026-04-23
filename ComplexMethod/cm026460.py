async def _async_update_data(self) -> CoordinatorData:
        """Fetch data from API."""

        data: CoordinatorData = {}

        if not self._api_calls:
            return data

        valid = False
        exception: Exception | None = None

        results = await asyncio.gather(
            *(call() for call in self._api_calls), return_exceptions=True
        )

        for result in results:
            if isinstance(result, VolvoAuthException):
                # If one result is a VolvoAuthException, then probably all requests
                # will fail. In this case we can cancel everything to
                # reauthenticate.
                #
                # Raising ConfigEntryAuthFailed will cancel future updates
                # and start a config flow with SOURCE_REAUTH (async_step_reauth)
                _LOGGER.debug(
                    "%s - Authentication failed. %s",
                    self.config_entry.entry_id,
                    result.message,
                )
                raise ConfigEntryAuthFailed(
                    translation_domain=DOMAIN,
                    translation_key="unauthorized",
                    translation_placeholders={"message": result.message},
                ) from result

            if isinstance(result, VolvoApiException):
                # Maybe it's just one call that fails. Log the error and
                # continue processing the other calls.
                _LOGGER.debug(
                    "%s - Error during data update: %s",
                    self.config_entry.entry_id,
                    result.message,
                )
                exception = exception or result
                continue

            if isinstance(result, Exception):
                # Something bad happened, raise immediately.
                raise UpdateFailed(
                    translation_domain=DOMAIN,
                    translation_key="update_failed",
                ) from result

            api_data = cast(CoordinatorData, result)
            data |= {
                key: field
                for key, field in api_data.items()
                if not _is_invalid_api_field(field)
            }

            valid = True

        # Raise an error if not a single API call succeeded
        if not valid:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
            ) from exception

        return data