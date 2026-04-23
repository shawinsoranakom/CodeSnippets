async def async_step_camera_auth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that gives the user option to set camera credentials."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}
        device = self._discovered_device
        assert device

        if user_input:
            live_view = user_input[CONF_LIVE_VIEW]
            if not live_view:
                return self._async_create_or_update_entry_from_device(
                    device, camera_data={CONF_LIVE_VIEW: False}
                )

            un = user_input.get(CONF_USERNAME)
            pw = user_input.get(CONF_PASSWORD)

        if user_input and un and pw:
            camera_creds = Credentials(un, cast(str, pw))

            camera_module = device.modules[Module.Camera]
            rtsp_url = camera_module.stream_rtsp_url(camera_creds)
            assert rtsp_url

            # If camera fails to create HLS stream via 'stream' then try
            # ffmpeg.async_get_image as some cameras do not work with HLS
            # and the frontend will fallback to mpeg on error
            try:
                await stream.async_check_stream_client_error(self.hass, rtsp_url)
            except stream.StreamOpenClientError as ex:
                if ex.error_code is stream.StreamClientError.Unauthorized:
                    errors["base"] = "invalid_camera_auth"
                else:
                    _LOGGER.debug(
                        "Device %s client error checking stream: %s", device.host, ex
                    )
                    if await ffmpeg.async_get_image(self.hass, rtsp_url):
                        return self._create_camera_entry(device, un, pw)

                    errors["base"] = "cannot_connect_camera"
                    placeholders["error"] = str(ex)
            except Exception as ex:  # noqa: BLE001
                _LOGGER.debug("Device %s error checking stream: %s", device.host, ex)
                if await ffmpeg.async_get_image(self.hass, rtsp_url):
                    return self._create_camera_entry(device, un, pw)

                errors["base"] = "cannot_connect_camera"
                placeholders["error"] = str(ex)
            else:
                return self._create_camera_entry(device, un, pw)

        elif user_input:
            errors["base"] = "camera_creds"

        entry = None
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
        elif self.source == SOURCE_REAUTH:
            entry = self._get_reauth_entry()

        if entry:
            placeholders[CONF_NAME] = entry.data[CONF_ALIAS]
            placeholders[CONF_MODEL] = entry.data[CONF_MODEL]
            placeholders[CONF_HOST] = entry.data[CONF_HOST]

        if user_input:
            form_data = {**user_input}
        elif entry:
            form_data = {**entry.data.get(CONF_CAMERA_CREDENTIALS, {})}
            form_data[CONF_LIVE_VIEW] = entry.data.get(CONF_LIVE_VIEW, False)
        else:
            form_data = {}

        self.context["title_placeholders"] = placeholders
        return self.async_show_form(
            step_id="camera_auth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_CAMERA_AUTH_DATA_SCHEMA, form_data
            ),
            errors=errors,
            description_placeholders=placeholders,
        )