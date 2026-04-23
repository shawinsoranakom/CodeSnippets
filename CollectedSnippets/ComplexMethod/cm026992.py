async def post(self, request: web.Request, device_id: str) -> web.Response:
        """Handle upload."""
        hass = request.app[KEY_HASS]

        try:
            node = async_get_node_from_device_id(hass, device_id, self._dev_reg)
        except ValueError as err:
            if "not loaded" in err.args[0]:
                raise web_exceptions.HTTPBadRequest from err
            raise web_exceptions.HTTPNotFound from err

        # If this was not true, we wouldn't have been able to get the node from the
        # device ID above
        assert node.client.driver

        # Increase max payload
        request._client_max_size = 1024 * 1024 * 10  # noqa: SLF001

        data = await request.post()

        if "file" not in data or not isinstance(data["file"], web_request.FileField):
            raise web_exceptions.HTTPBadRequest

        uploaded_file: web_request.FileField = data["file"]

        try:
            if node.client.driver.controller.own_node == node:
                await driver_firmware_update_otw(
                    node.client.ws_server_url,
                    DriverFirmwareUpdateData(
                        uploaded_file.filename,
                        await hass.async_add_executor_job(uploaded_file.file.read),
                    ),
                    async_get_clientsession(hass),
                    additional_user_agent_components=USER_AGENT,
                )
            else:
                firmware_target: int | None = None
                if "target" in data:
                    firmware_target = int(cast(str, data["target"]))
                await update_firmware(
                    node.client.ws_server_url,
                    node,
                    [
                        NodeFirmwareUpdateData(
                            uploaded_file.filename,
                            await hass.async_add_executor_job(uploaded_file.file.read),
                            firmware_target=firmware_target,
                        )
                    ],
                    async_get_clientsession(hass),
                    additional_user_agent_components=USER_AGENT,
                )
        except BaseZwaveJSServerError as err:
            raise web_exceptions.HTTPBadRequest(reason=str(err)) from err

        return self.json(None)