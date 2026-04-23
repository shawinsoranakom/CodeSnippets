def service_handler(service: ServiceCall) -> None:
        """Apply a service.

        We key this using the router URL instead of its unique id / serial number,
        because the latter is not available anywhere in the UI.
        """
        routers = hass.data[DOMAIN].routers
        if url := service.data.get(CONF_URL):
            router = next(
                (router for router in routers.values() if router.url == url), None
            )
        elif not routers:
            _LOGGER.error("%s: no routers configured", service.service)
            return
        elif len(routers) == 1:
            router = next(iter(routers.values()))
        else:
            _LOGGER.error(
                "%s: more than one router configured, must specify one of URLs %s",
                service.service,
                sorted(router.url for router in routers.values()),
            )
            return
        if not router:
            _LOGGER.error("%s: router %s unavailable", service.service, url)
            return

        if service.service == SERVICE_RESUME_INTEGRATION:
            # Login will be handled automatically on demand
            router.suspended = False
            _LOGGER.debug("%s: %s", service.service, "done")
        elif service.service == SERVICE_SUSPEND_INTEGRATION:
            router.logout()
            router.suspended = True
            _LOGGER.debug("%s: %s", service.service, "done")
        else:
            _LOGGER.error("%s: unsupported service", service.service)