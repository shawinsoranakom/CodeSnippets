async def _async_update_data(self) -> None:
        """Fetch data from the Pi-hole API."""
        try:
            await self._api.get_data()
            await self._api.get_versions()
            if "error" in (response := self._api.data):
                match response["error"]:
                    case {
                        "key": key,
                        "message": message,
                        "hint": hint,
                    } if (
                        key == VERSION_6_RESPONSE_TO_5_ERROR["key"]
                        and message == VERSION_6_RESPONSE_TO_5_ERROR["message"]
                        and hint.startswith("The API is hosted at ")
                        and "/admin/api" in hint
                    ):
                        _LOGGER.warning(
                            "Pi-hole API v6 returned an error that is expected when using v5 endpoints please re-configure your authentication"
                        )
                        raise ConfigEntryAuthFailed
        except HoleError as err:
            if str(err) == "Authentication failed: Invalid password":
                raise ConfigEntryAuthFailed(
                    f"Pi-hole {self._name} at host {self._host}, reported an invalid password"
                ) from err
            raise UpdateFailed(
                f"Pi-hole {self._name} at host {self._host}, update failed with HoleError: {err}"
            ) from err
        if not isinstance(self._api.data, dict):
            raise ConfigEntryAuthFailed(
                f"Pi-hole {self._name} at host {self._host}, returned an unexpected response: {self._api.data}, assuming authentication failed"
            )