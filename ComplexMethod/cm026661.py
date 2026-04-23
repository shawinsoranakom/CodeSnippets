async def _async_update_data(self) -> FingDataObject:
        """Fetch data from Fing Agent."""
        device_response = None
        agent_info_response = None
        try:
            device_response = await self._fing.get_devices()

            if self._upnp_available:
                agent_info_response = await self._fing.get_agent_info()

        except httpx.NetworkError as err:
            raise UpdateFailed("Failed to connect") from err
        except httpx.TimeoutException as err:
            raise UpdateFailed("Timeout establishing connection") from err
        except httpx.HTTPStatusError as err:
            if err.response.status_code == 401:
                raise UpdateFailed("Invalid API key") from err
            raise UpdateFailed(
                f"Http request failed -> {err.response.status_code} - {err.response.reason_phrase}"
            ) from err
        except httpx.InvalidURL as err:
            raise UpdateFailed("Invalid hostname or IP address") from err
        except (
            httpx.HTTPError,
            httpx.CookieConflict,
            httpx.StreamError,
        ) as err:
            raise UpdateFailed("Unexpected error from HTTP request") from err
        else:
            return FingDataObject(
                device_response.network_id,
                agent_info_response,
                {device.mac: device for device in device_response.devices},
            )