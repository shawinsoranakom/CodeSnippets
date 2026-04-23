def _log_object_sources(
    max_objects: int, last_ids: set[int], last_stats: dict[str, int]
) -> None:
    # Imports deferred to avoid loading modules
    # in memory since usually only one part of this
    # integration is used at a time
    import gc  # noqa: PLC0415

    gc.collect()

    objects = gc.get_objects()
    new_objects: list[object] = []
    new_objects_overflow: dict[str, int] = {}
    current_ids = set()
    new_stats: dict[str, int] = {}
    had_new_object_growth = False
    try:
        for _object in objects:
            object_type = type(_object).__name__
            new_stats[object_type] = new_stats.get(object_type, 0) + 1

        for _object in objects:
            id_ = id(_object)
            current_ids.add(id_)
            if id_ in last_ids:
                continue
            object_type = type(_object).__name__
            if last_stats.get(object_type, 0) < new_stats[object_type]:
                if len(new_objects) < max_objects:
                    new_objects.append(_object)
                else:
                    new_objects_overflow.setdefault(object_type, 0)
                    new_objects_overflow[object_type] += 1

        for _object in new_objects:
            had_new_object_growth = True
            object_type = type(_object).__name__
            _LOGGER.critical(
                "New object %s (%s/%s) at %s: %s",
                object_type,
                last_stats.get(object_type, 0),
                new_stats[object_type],
                _get_function_absfile(_object) or _find_backrefs_not_to_self(_object),
                _safe_repr(_object),
            )

        for object_type, count in last_stats.items():
            new_stats[object_type] = max(new_stats.get(object_type, 0), count)
    finally:
        # Break reference cycles
        del objects
        del new_objects
        last_ids.clear()
        last_ids.update(current_ids)
        last_stats.clear()
        last_stats.update(new_stats)
        del new_stats
        del current_ids

    if new_objects_overflow:
        _LOGGER.critical("New objects overflowed by %s", new_objects_overflow)
    elif not had_new_object_growth:
        _LOGGER.critical("No new object growth found")