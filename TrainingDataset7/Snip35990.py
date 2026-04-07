def skip_unless_watchman_available():
    try:
        autoreload.WatchmanReloader.check_availability()
    except WatchmanUnavailable as e:
        return skip("Watchman unavailable: %s" % e)
    return lambda func: func