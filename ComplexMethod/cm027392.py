async def post(self, request: Request, data: dict) -> Response:
        """Handle the POST request for registration."""
        hass = request.app[KEY_HASS]

        webhook_id = secrets.token_hex()
        user = request["hass_user"]

        if (
            not user.local_only
            and cloud.async_active_subscription(hass)
            and cloud.async_is_connected(hass)
        ):
            data[CONF_CLOUDHOOK_URL] = await async_create_cloud_hook(
                hass, webhook_id, None
            )

        data[CONF_WEBHOOK_ID] = webhook_id

        if data[ATTR_SUPPORTS_ENCRYPTION]:
            data[CONF_SECRET] = secrets.token_hex(SecretBox.KEY_SIZE)

        data[CONF_USER_ID] = user.id

        # Fallback to DEVICE_ID if slug is empty.
        if not slugify(data[ATTR_DEVICE_NAME], separator=""):
            data[ATTR_DEVICE_NAME] = data[ATTR_DEVICE_ID]

        await hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, data=data, context={"source": "registration"}
            )
        )

        remote_ui_url = None
        if not user.local_only and cloud.async_active_subscription(hass):
            with suppress(cloud.CloudNotAvailable):
                remote_ui_url = cloud.async_remote_ui_url(hass)

        return self.json(
            {
                CONF_CLOUDHOOK_URL: data.get(CONF_CLOUDHOOK_URL),
                CONF_REMOTE_UI_URL: remote_ui_url,
                CONF_SECRET: data.get(CONF_SECRET),
                CONF_WEBHOOK_ID: data[CONF_WEBHOOK_ID],
            },
            status_code=HTTPStatus.CREATED,
        )