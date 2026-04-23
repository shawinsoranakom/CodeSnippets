async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Teltonika device."""
        modems = Modems(self.client.auth)
        try:
            # Get modems data using the teltasync library
            modems_response = await modems.get_status()
        except TeltonikaAuthenticationError as err:
            raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
        except (ClientResponseError, ContentTypeError) as err:
            if (isinstance(err, ClientResponseError) and err.status in (401, 403)) or (
                isinstance(err, ContentTypeError) and err.status == 403
            ):
                raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
            raise UpdateFailed(f"Error communicating with device: {err}") from err
        except TeltonikaConnectionError as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

        if not modems_response.success:
            if modems_response.errors and any(
                error.code in AUTH_ERROR_CODES for error in modems_response.errors
            ):
                raise ConfigEntryAuthFailed(
                    "Authentication failed: unauthorized access"
                )

            error_message = (
                modems_response.errors[0].error
                if modems_response.errors
                else "Unknown API error"
            )
            raise UpdateFailed(f"Error communicating with device: {error_message}")

        # Return only modems which are online
        modem_data: dict[str, Any] = {}
        if modems_response.data:
            modem_data.update(
                {
                    modem.id: modem
                    for modem in modems_response.data
                    if Modems.is_online(modem)
                }
            )

        return modem_data