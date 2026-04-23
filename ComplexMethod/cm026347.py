async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Discover and setup Xeoma Cameras."""

    host = config[CONF_HOST]
    login = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    xeoma = Xeoma(host, login, password)

    try:
        await xeoma.async_test_connection()
        discovered_image_names = await xeoma.async_get_image_names()
        discovered_cameras = [
            {
                CONF_IMAGE_NAME: image_name,
                CONF_HIDE: False,
                CONF_NAME: image_name,
                CONF_VIEWER_USERNAME: username,
                CONF_VIEWER_PASSWORD: pw,
            }
            for image_name, username, pw in discovered_image_names
        ]

        for cam in config.get(CONF_CAMERAS, []):
            camera = next(
                (
                    dc
                    for dc in discovered_cameras
                    if dc[CONF_IMAGE_NAME] == cam[CONF_IMAGE_NAME]
                ),
                None,
            )

            if camera is not None:
                if CONF_NAME in cam:
                    camera[CONF_NAME] = cam[CONF_NAME]
                if CONF_HIDE in cam:
                    camera[CONF_HIDE] = cam[CONF_HIDE]

        cameras = list(filter(lambda c: not c[CONF_HIDE], discovered_cameras))
        async_add_entities(
            [
                XeomaCamera(
                    xeoma,
                    camera[CONF_IMAGE_NAME],
                    camera[CONF_NAME],
                    camera[CONF_VIEWER_USERNAME],
                    camera[CONF_VIEWER_PASSWORD],
                )
                for camera in cameras
            ]
        )
    except XeomaError as err:
        _LOGGER.error("Error: %s", err.message)
        return