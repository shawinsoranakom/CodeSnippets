async def async_init(self) -> None:
        """Connect to Reolink host."""
        if not self._api.valid_password():
            if (
                len(self._config[CONF_PASSWORD]) >= 32
                and self._config_entry is not None
            ):
                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    f"password_too_long_{self._config_entry.entry_id}",
                    is_fixable=True,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="password_too_long",
                    translation_placeholders={"name": self._config_entry.title},
                )

            raise PasswordIncompatible(
                "Reolink password contains incompatible special character or "
                "is too long, please change the password to only contain characters: "
                f"a-z, A-Z, 0-9 or {ALLOWED_SPECIAL_CHARS} "
                "and not be longer than 31 characters"
            )

        store: Store[str] | None = None
        if self._config_entry is not None:
            ir.async_delete_issue(
                self._hass, DOMAIN, f"password_too_long_{self._config_entry.entry_id}"
            )
            store = get_store(self._hass, self._config_entry.entry_id)
            if self._config.get(CONF_SUPPORTS_PRIVACY_MODE) and (
                data := await store.async_load()
            ):
                self._api.set_raw_host_data(data)

        await self._api.get_host_data()

        if self._api.mac_address is None:
            raise ReolinkSetupException("Could not get mac address")

        if not self._api.is_admin:
            raise UserNotAdmin(
                f"User '{self._api.username}' has authorization level "
                f"'{self._api.user_level}', only admin users can change camera settings"
            )

        self.privacy_mode = self._api.baichuan.privacy_mode()

        if (
            store
            and self._api.supported(None, "privacy_mode")
            and not self.privacy_mode
        ):
            _LOGGER.debug(
                "Saving raw host data for next reload in case privacy mode is enabled"
            )
            data = self._api.get_raw_host_data()
            await store.async_save(data)

        onvif_supported = self._api.supported(None, "ONVIF")
        self._onvif_push_supported = onvif_supported
        self._onvif_long_poll_supported = onvif_supported

        enable_rtsp = None
        enable_onvif = None
        enable_rtmp = None

        if not self._api.rtsp_enabled and self._api.supported(None, "RTSP"):
            _LOGGER.debug(
                "RTSP is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_rtsp = True

        if not self._api.onvif_enabled and onvif_supported:
            _LOGGER.debug(
                "ONVIF is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_onvif = True

        if (
            not self._api.rtmp_enabled
            and self._api.protocol == "rtmp"
            and not self._api.baichuan_only
        ):
            _LOGGER.debug(
                "RTMP is disabled on %s, trying to enable it", self._api.nvr_name
            )
            enable_rtmp = True

        if enable_onvif or enable_rtmp or enable_rtsp:
            try:
                await self._api.set_net_port(
                    enable_onvif=enable_onvif,
                    enable_rtmp=enable_rtmp,
                    enable_rtsp=enable_rtsp,
                )
            except ReolinkError:
                ports = ""
                if enable_rtsp:
                    ports += "RTSP "

                if enable_onvif:
                    ports += "ONVIF "

                if enable_rtmp:
                    ports += "RTMP "

                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    "enable_port",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="enable_port",
                    translation_placeholders={
                        "name": self._api.nvr_name,
                        "ports": ports,
                        "info_link": "https://support.reolink.com/hc/en-us/articles/900004435763-How-to-Set-up-Reolink-Ports-Settings-via-Reolink-Client-New-Client-",
                    },
                )
        else:
            ir.async_delete_issue(self._hass, DOMAIN, "enable_port")

        if self._api.supported(None, "UID"):
            self._unique_id = self._api.uid
        else:
            self._unique_id = format_mac(self._api.mac_address)

        try:
            await self._api.baichuan.subscribe_events()
        except ReolinkError:
            await self._async_check_tcp_push()
        else:
            self._cancel_tcp_push_check = async_call_later(
                self._hass, FIRST_TCP_PUSH_TIMEOUT, self._async_check_tcp_push
            )

        ch_list: list[int | None] = [None]
        if self._api.is_nvr:
            ch_list.extend(self._api.channels)
        for ch in ch_list:
            if not self._api.supported(ch, "firmware"):
                continue

            key = ch if ch is not None else "host"
            if self._api.camera_sw_version_update_required(ch):
                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    f"firmware_update_{key}",
                    is_fixable=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="firmware_update",
                    translation_placeholders={
                        "required_firmware": self._api.camera_sw_version_required(
                            ch
                        ).version_string,
                        "current_firmware": self._api.camera_sw_version(ch),
                        "model": self._api.camera_model(ch),
                        "hw_version": self._api.camera_hardware_version(ch),
                        "name": self._api.camera_name(ch),
                        "download_link": "https://reolink.com/download-center/",
                    },
                )
            else:
                ir.async_delete_issue(self._hass, DOMAIN, f"firmware_update_{key}")