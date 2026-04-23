def check_availability(cls):
        if not pywatchman:
            raise WatchmanUnavailable("pywatchman not installed.")
        client = pywatchman.client(timeout=0.1)
        try:
            result = client.capabilityCheck()
        except Exception:
            # The service is down?
            raise WatchmanUnavailable("Cannot connect to the watchman service.")
        version = get_version_tuple(result["version"])
        # Watchman 4.9 includes multiple improvements to watching project
        # directories as well as case insensitive filesystems.
        logger.debug("Watchman version %s", version)
        if version < (4, 9):
            raise WatchmanUnavailable("Watchman 4.9 or later is required.")