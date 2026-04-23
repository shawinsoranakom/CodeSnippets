async def _async_get_nvr_data(
        self,
        user_input: dict[str, Any],
    ) -> tuple[NVR | None, dict[str, str]]:
        session = async_create_clientsession(
            self.hass, cookie_jar=CookieJar(unsafe=True)
        )
        public_api_session = async_get_clientsession(self.hass)

        host = user_input[CONF_HOST]
        port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
        verify_ssl = user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)

        protect = ProtectApiClient(
            session=session,
            public_api_session=public_api_session,
            host=host,
            port=port,
            username=user_input[CONF_USERNAME],
            password=user_input[CONF_PASSWORD],
            api_key=user_input.get(CONF_API_KEY, ""),
            verify_ssl=verify_ssl,
            cache_dir=Path(self.hass.config.path(STORAGE_DIR, "unifiprotect")),
            config_dir=Path(self.hass.config.path(STORAGE_DIR, "unifiprotect")),
        )

        errors = {}
        nvr_data = None
        try:
            bootstrap = await protect.get_bootstrap()
            nvr_data = bootstrap.nvr
        except NotAuthorized as ex:
            _LOGGER.debug(ex)
            errors[CONF_PASSWORD] = "invalid_auth"
        except ClientError as ex:
            _LOGGER.error(ex)
            errors["base"] = "cannot_connect"
        else:
            if nvr_data.version < MIN_REQUIRED_PROTECT_V:
                _LOGGER.debug(
                    OUTDATED_LOG_MESSAGE,
                    nvr_data.version,
                    MIN_REQUIRED_PROTECT_V,
                )
                errors["base"] = "protect_version"

            auth_user = bootstrap.users.get(bootstrap.auth_user_id)
            if auth_user and auth_user.cloud_account:
                errors["base"] = "cloud_user"

        # Only validate API key if bootstrap succeeded
        if nvr_data and not errors:
            try:
                await protect.get_meta_info()
            except NotAuthorized as ex:
                _LOGGER.debug(ex)
                errors[CONF_API_KEY] = "invalid_auth"
            except ClientError as ex:
                _LOGGER.error(ex)
                errors["base"] = "cannot_connect"

        return nvr_data, errors