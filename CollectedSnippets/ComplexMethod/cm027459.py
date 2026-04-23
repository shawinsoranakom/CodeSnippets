async def async_validate_input_create_entry(
        self, user_input: dict[str, Any], step_id: str
    ) -> ConfigFlowResult:
        """Process user input and create new or update existing config entry."""
        host = user_input[CONF_HOST]
        port = user_input.get(CONF_PORT)
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        use_ssl = user_input.get(CONF_SSL, DEFAULT_USE_SSL)
        verify_ssl = user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
        otp_code = user_input.get(CONF_OTP_CODE)
        friendly_name = user_input.get(CONF_NAME)
        backup_path = user_input.get(CONF_BACKUP_PATH)
        backup_share = user_input.get(CONF_BACKUP_SHARE)

        if not port:
            if use_ssl is True:
                port = DEFAULT_PORT_SSL
            else:
                port = DEFAULT_PORT

        if self.api is None:
            session = async_get_clientsession(self.hass, verify_ssl)
            self.api = SynologyDSM(
                session,
                host,
                port,
                username,
                password,
                use_ssl,
                timeout=DEFAULT_TIMEOUT,
            )

        errors = {}
        try:
            serial = await _login_and_fetch_syno_info(self.api, otp_code)
        except SynologyDSMLogin2SARequiredException:
            return await self.async_step_2sa(user_input)
        except SynologyDSMLogin2SAFailedException:
            errors[CONF_OTP_CODE] = "otp_failed"
            user_input[CONF_OTP_CODE] = None
            return await self.async_step_2sa(user_input, errors)
        except SynologyDSMLoginInvalidException as ex:
            _LOGGER.error(ex)
            errors[CONF_USERNAME] = "invalid_auth"
        except SynologyDSMRequestException as ex:
            _LOGGER.error(ex)
            errors[CONF_HOST] = "cannot_connect"
        except SynologyDSMException as ex:
            _LOGGER.error(ex)
            errors["base"] = "unknown"
        except InvalidData:
            errors["base"] = "missing_data"

        if errors:
            self.api = None
            return self._show_form(step_id, user_input, errors)

        with suppress(*SYNOLOGY_CONNECTION_EXCEPTIONS):
            self.shares = await self.api.file.get_shared_folders(only_writable=True)

        if self.shares and not backup_path:
            return await self.async_step_backup_share(user_input)

        # unique_id should be serial for services purpose
        existing_entry = await self.async_set_unique_id(serial, raise_on_progress=False)

        config_data = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_SSL: use_ssl,
            CONF_VERIFY_SSL: verify_ssl,
            CONF_USERNAME: username,
            CONF_PASSWORD: password,
            CONF_MAC: self.api.network.macs,
        }
        config_options = {
            CONF_BACKUP_PATH: backup_path,
            CONF_BACKUP_SHARE: backup_share,
        }
        if otp_code:
            config_data[CONF_DEVICE_TOKEN] = self.api.device_token
        if user_input.get(CONF_DISKS):
            config_data[CONF_DISKS] = user_input[CONF_DISKS]
        if user_input.get(CONF_VOLUMES):
            config_data[CONF_VOLUMES] = user_input[CONF_VOLUMES]

        if existing_entry:
            reason = (
                "reauth_successful" if self.reauth_conf else "reconfigure_successful"
            )
            return self.async_update_reload_and_abort(
                existing_entry, data=config_data, options=config_options, reason=reason
            )

        return self.async_create_entry(
            title=friendly_name or host, data=config_data, options=config_options
        )