async def _async_update_data(self) -> None:
        """Fetch data from Rituals, with one silent re-auth on 401.

        If silent re-auth also fails, raise ConfigEntryAuthFailed to trigger reauth flow.
        Other HTTP/network errors are wrapped in UpdateFailed so HA can retry.
        """
        try:
            await self.diffuser.update_data()
        except (AuthenticationException, ClientResponseError) as err:
            # Treat 401/403 like AuthenticationException → one silent re-auth, single retry
            if isinstance(err, ClientResponseError) and (status := err.status) not in (
                401,
                403,
            ):
                # Non-auth HTTP error → let HA retry
                raise UpdateFailed(f"HTTP {status}") from err

            self.logger.debug(
                "Auth issue detected (%r). Attempting silent re-auth.", err
            )
            try:
                await self.account.authenticate()
                await self.diffuser.update_data()
            except AuthenticationException as err2:
                # Credentials invalid → trigger HA reauth
                raise ConfigEntryAuthFailed from err2
            except ClientResponseError as err2:
                # Still HTTP auth errors after refresh → trigger HA reauth
                if err2.status in (401, 403):
                    raise ConfigEntryAuthFailed from err2
                raise UpdateFailed(f"HTTP {err2.status}") from err2
        except ClientError as err:
            # Network issues (timeouts, DNS, etc.)
            raise UpdateFailed(f"Network error: {err!r}") from err