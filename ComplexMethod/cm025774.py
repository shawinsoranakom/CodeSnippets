async def async_setup_platform(
        integration_name: str,
        p_config: ConfigType | None = None,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up a notify platform."""
        if p_config is None:
            p_config = {}

        platform = cast(
            LegacyNotifyPlatform | None,
            await async_prepare_setup_platform(hass, config, DOMAIN, integration_name),
        )

        if platform is None:
            LOGGER.error("Unknown notification service specified")
            return

        full_name = f"{DOMAIN}.{integration_name}"
        LOGGER.info("Setting up %s", full_name)
        with async_start_setup(
            hass,
            integration=integration_name,
            group=str(id(p_config)),
            phase=SetupPhases.PLATFORM_SETUP,
        ):
            notify_service: BaseNotificationService | None = None
            try:
                if hasattr(platform, "async_get_service"):
                    notify_service = await platform.async_get_service(
                        hass, p_config, discovery_info
                    )
                elif hasattr(platform, "get_service"):
                    notify_service = await hass.async_add_executor_job(
                        platform.get_service, hass, p_config, discovery_info
                    )
                else:
                    raise HomeAssistantError("Invalid notify platform.")  # noqa: TRY301

                if notify_service is None:
                    # Platforms can decide not to create a service based
                    # on discovery data.
                    if discovery_info is None:
                        LOGGER.error(
                            "Failed to initialize notification service %s",
                            integration_name,
                        )
                    return

            except Exception:  # noqa: BLE001
                LOGGER.exception("Error setting up platform %s", integration_name)
                return

            if discovery_info is None:
                discovery_info = {}

            conf_name = p_config.get(CONF_NAME) or discovery_info.get(CONF_NAME)
            target_service_name_prefix = conf_name or integration_name
            service_name = slugify(conf_name or SERVICE_NOTIFY)

            await notify_service.async_setup(
                hass, service_name, target_service_name_prefix
            )
            await notify_service.async_register_services()

            hass.data[NOTIFY_SERVICES].setdefault(integration_name, []).append(
                notify_service
            )
            hass.config.components.add(f"{integration_name}.{DOMAIN}")