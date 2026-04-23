async def _async_update_data(self):
        try:
            async with timeout(DEFAULT_TIMEOUT):
                # The following command might fail in case of the panel is offline.
                # We handle this case in the following exception blocks.
                status = await self._client.get_current_panel_status()

        except ElmaxBadPinError as err:
            raise ConfigEntryAuthFailed("Control panel pin was refused") from err
        except ElmaxBadLoginError as err:
            raise ConfigEntryAuthFailed("Refused username/password/pin") from err
        except ElmaxApiError as err:
            raise UpdateFailed(f"Error communicating with ELMAX API: {err}") from err
        except ElmaxPanelBusyError as err:
            raise UpdateFailed(
                "Communication with the panel failed, as it is currently busy"
            ) from err
        except (ConnectError, ConnectTimeout, ElmaxNetworkError) as err:
            if isinstance(self._client, Elmax):
                raise UpdateFailed(
                    "A communication error has occurred. "
                    "Make sure HA can reach the internet and that "
                    "your firewall allows communication with the Meross Cloud."
                ) from err

            raise UpdateFailed(
                "A communication error has occurred. "
                "Make sure the panel is online and that  "
                "your firewall allows communication with it."
            ) from err

        # Store a dictionary for fast endpoint state access
        self._state_by_endpoint = {k.endpoint_id: k for k in status.all_endpoints}

        # If panel supports it and a it hasn't been registered yet, register the push notification handler
        if status.push_feature and self._push_notification_handler is None:
            self._register_push_notification_handler()

        self._fire_data_update(status)
        return status