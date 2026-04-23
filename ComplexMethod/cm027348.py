def _lru_stats(call: ServiceCall) -> None:
        """Log the stats of all lru caches."""
        # Imports deferred to avoid loading modules
        # in memory since usually only one part of this
        # integration is used at a time
        import objgraph  # noqa: PLC0415

        for lru in objgraph.by_type(_LRU_CACHE_WRAPPER_OBJECT):
            lru = cast(_lru_cache_wrapper, lru)
            _LOGGER.critical(
                "Cache stats for lru_cache %s at %s: %s",
                lru.__wrapped__,
                _get_function_absfile(lru.__wrapped__) or "unknown",
                lru.cache_info(),
            )

        for _class in _KNOWN_LRU_CLASSES:
            for class_with_lru_attr in objgraph.by_type(_class):
                for maybe_lru in class_with_lru_attr.__dict__.values():
                    if isinstance(maybe_lru, LRU):
                        _LOGGER.critical(
                            "Cache stats for LRU %s at %s: %s",
                            type(class_with_lru_attr),
                            _get_function_absfile(class_with_lru_attr) or "unknown",
                            maybe_lru.get_stats(),
                        )

        for lru in objgraph.by_type(_SQLALCHEMY_LRU_OBJECT):
            if (data := getattr(lru, "_data", None)) and isinstance(data, dict):
                for key, value in dict(data).items():
                    _LOGGER.critical(
                        "Cache data for sqlalchemy LRUCache %s: %s: %s", lru, key, value
                    )

        persistent_notification.create(
            hass,
            (
                "LRU cache states have been dumped to the log. See [the"
                " logs](/config/logs) to review the stats."
            ),
            title="LRU stats completed",
            notification_id="profile_lru_stats",
        )