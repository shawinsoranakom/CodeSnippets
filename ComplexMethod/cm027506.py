def async_add_new_entities(
    router: Router,
    async_add_entities: AddConfigEntryEntitiesCallback,
    tracked: set[str],
) -> None:
    """Add new entities that are not already being tracked."""
    if not (hosts := _get_hosts(router)):
        return

    track_wired_clients = router.config_entry.options.get(
        CONF_TRACK_WIRED_CLIENTS, DEFAULT_TRACK_WIRED_CLIENTS
    )

    new_entities: list[Entity] = []
    for host in (
        x
        for x in hosts
        if not _is_us(x)
        and _is_connected(x)
        and x.get("MacAddress")
        and (track_wired_clients or _is_wireless(x))
    ):
        entity = HuaweiLteScannerEntity(router, host["MacAddress"])
        if entity.unique_id in tracked:
            continue
        tracked.add(entity.unique_id)
        new_entities.append(entity)
    async_add_entities(new_entities, True)