async def _async_step_credentials(
        self,
        step_id: str,
        entry: ConfigEntry,
        user_input: dict[str, Any] | None,
    ) -> ConfigFlowResult:
        """Handle credential update for both reauth and reconfigure."""
        errors: dict[str, str] = {}

        if user_input is not None:
            auth_type = entry.data.get(CONF_AUTH_TYPE)

            if auth_type == AUTH_PASSWORD:
                server_url = SERVER_URLS_NAMES[user_input[CONF_REGION]]
                api = growattServer.GrowattApi(
                    add_random_user_id=True,
                    agent_identifier=user_input[CONF_USERNAME],
                )
                api.server_url = server_url

                try:
                    login_response = await self.hass.async_add_executor_job(
                        api.login, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    )
                except requests.exceptions.RequestException as ex:
                    _LOGGER.debug("Network error during credential update: %s", ex)
                    errors["base"] = ERROR_CANNOT_CONNECT
                except (ValueError, KeyError, TypeError, AttributeError) as ex:
                    _LOGGER.debug(
                        "Invalid response format during credential update: %s", ex
                    )
                    errors["base"] = ERROR_CANNOT_CONNECT
                else:
                    if not isinstance(login_response, dict):
                        errors["base"] = ERROR_CANNOT_CONNECT
                    elif login_response.get("success"):
                        return self.async_update_reload_and_abort(
                            entry,
                            data_updates={
                                CONF_USERNAME: user_input[CONF_USERNAME],
                                CONF_PASSWORD: user_input[CONF_PASSWORD],
                                CONF_URL: server_url,
                            },
                        )
                    elif login_response.get("msg") == LOGIN_INVALID_AUTH_CODE:
                        errors["base"] = ERROR_INVALID_AUTH
                    else:
                        errors["base"] = ERROR_CANNOT_CONNECT

            elif auth_type == AUTH_API_TOKEN:
                server_url = SERVER_URLS_NAMES[user_input[CONF_REGION]]
                api = growattServer.OpenApiV1(token=user_input[CONF_TOKEN])
                api.server_url = server_url

                try:
                    await self.hass.async_add_executor_job(api.plant_list)
                except requests.exceptions.RequestException as ex:
                    _LOGGER.debug("Network error during credential update: %s", ex)
                    errors["base"] = ERROR_CANNOT_CONNECT
                except growattServer.GrowattV1ApiError as err:
                    if err.error_code == V1_API_ERROR_NO_PRIVILEGE:
                        errors["base"] = ERROR_INVALID_AUTH
                    else:
                        _LOGGER.debug(
                            "Growatt V1 API error during credential update: %s (Code: %s)",
                            err.error_msg or str(err),
                            err.error_code,
                        )
                        errors["base"] = ERROR_CANNOT_CONNECT
                except (ValueError, KeyError, TypeError, AttributeError) as ex:
                    _LOGGER.debug(
                        "Invalid response format during credential update: %s", ex
                    )
                    errors["base"] = ERROR_CANNOT_CONNECT
                else:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_TOKEN: user_input[CONF_TOKEN],
                            CONF_URL: server_url,
                        },
                    )

        # Determine the current region key from the stored config value.
        # Legacy entries may store the region key directly; newer entries store the URL.
        stored_url = entry.data.get(CONF_URL, "")
        if stored_url in SERVER_URLS_NAMES:
            current_region = stored_url
        else:
            current_region = _URL_TO_REGION.get(stored_url, DEFAULT_URL)

        auth_type = entry.data.get(CONF_AUTH_TYPE)
        if auth_type == AUTH_PASSWORD:
            data_schema = vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=entry.data.get(CONF_USERNAME),
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_REGION, default=current_region): SelectSelector(
                        SelectSelectorConfig(
                            options=list(SERVER_URLS_NAMES.keys()),
                            translation_key="region",
                        )
                    ),
                }
            )
        elif auth_type == AUTH_API_TOKEN:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_TOKEN): str,
                    vol.Required(CONF_REGION, default=current_region): SelectSelector(
                        SelectSelectorConfig(
                            options=list(SERVER_URLS_NAMES.keys()),
                            translation_key="region",
                        )
                    ),
                }
            )
        else:
            return self.async_abort(reason=ERROR_CANNOT_CONNECT)

        if user_input is not None:
            data_schema = self.add_suggested_values_to_schema(
                data_schema,
                {
                    key: value
                    for key, value in user_input.items()
                    if key not in (CONF_PASSWORD, CONF_TOKEN)
                },
            )

        return self.async_show_form(
            step_id=step_id,
            data_schema=data_schema,
            errors=errors,
        )