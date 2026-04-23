async def _async_process_config(hass: HomeAssistant, config: ConfigType) -> bool:
    """Process rest configuration."""
    if DOMAIN not in config:
        return True

    refresh_coroutines: list[Coroutine[Any, Any, None]] = []
    load_coroutines: list[Coroutine[Any, Any, None]] = []
    rest_config: list[ConfigType] = config[DOMAIN]
    for rest_idx, conf in enumerate(rest_config):
        scan_interval: timedelta = conf.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        resource_template: template.Template | None = conf.get(CONF_RESOURCE_TEMPLATE)
        payload_template: template.Template | None = conf.get(CONF_PAYLOAD_TEMPLATE)
        rest = create_rest_data_from_config(hass, conf)
        coordinator = _rest_coordinator(
            hass, rest, resource_template, payload_template, scan_interval
        )
        refresh_coroutines.append(coordinator.async_refresh())
        hass.data[DOMAIN][REST_DATA].append({REST: rest, COORDINATOR: coordinator})

        for platform_domain in COORDINATOR_AWARE_PLATFORMS:
            if platform_domain not in conf:
                continue

            for platform_conf in conf[platform_domain]:
                hass.data[DOMAIN][platform_domain].append(platform_conf)
                platform_idx = len(hass.data[DOMAIN][platform_domain]) - 1

                load_coroutine = discovery.async_load_platform(
                    hass,
                    platform_domain,
                    DOMAIN,
                    {REST_IDX: rest_idx, PLATFORM_IDX: platform_idx},
                    config,
                )
                load_coroutines.append(load_coroutine)

    if refresh_coroutines:
        await asyncio.gather(*(create_eager_task(coro) for coro in refresh_coroutines))

    if load_coroutines:
        await asyncio.gather(*(create_eager_task(coro) for coro in load_coroutines))

    return True