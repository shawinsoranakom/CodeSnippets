async def _async_update_data(self) -> KioskerData:
        """Update data via library."""
        try:
            status, blackout, screensaver = await self.hass.async_add_executor_job(
                self._fetch_all_data
            )
        except AuthenticationError as exc:
            raise ConfigEntryAuthFailed(
                "Authentication failed. Check your API token."
            ) from exc
        except IPAuthenticationError as exc:
            raise ConfigEntryAuthFailed(
                "IP authentication failed. Check your IP whitelist."
            ) from exc
        except (ConnectionError, PingError) as exc:
            raise UpdateFailed(f"Connection failed: {exc}") from exc
        except TLSVerificationError as exc:
            raise UpdateFailed(f"TLS verification failed: {exc}") from exc
        except BadRequestError as exc:
            raise UpdateFailed(f"Bad request: {exc}") from exc
        except (OSError, TimeoutError) as exc:
            raise UpdateFailed(f"Connection timeout: {exc}") from exc
        except Exception as exc:
            _LOGGER.exception("Unexpected error updating Kiosker data")
            raise UpdateFailed(f"Unexpected error: {exc}") from exc

        return KioskerData(
            status=status,
            blackout=blackout,
            screensaver=screensaver,
        )