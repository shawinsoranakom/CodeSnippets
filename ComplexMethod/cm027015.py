async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for all known thread networks."""
    networks: dict[str, Network] = {}

    # Start with all networks that HA knows about
    store = await async_get_store(hass)
    for record in store.datasets.values():
        if not record.extended_pan_id:
            continue
        network = networks.setdefault(
            record.extended_pan_id,
            {
                "name": record.network_name,
                "routers": {},
                "prefixes": set(),
                "unexpected_routers": set(),
            },
        )
        if mlp_item := record.dataset.get(MeshcopTLVType.MESHLOCALPREFIX):
            # We know that it is indeed a /64 mesh-local IPv6 NETWORK because Thread spec;
            # However, the "prefixes" field contains no /XX (prefix length) in their entries ATM,
            # so we use an IPv6Address in order to get a "prefixes" entry with no prefix length.
            prefix_address = IPv6Address(mlp_item.data.ljust(16, b"\x00"))
            network["prefixes"].add(str(prefix_address))

    # Find all routes currently act that might be thread related, so we can match them to
    # border routers as we process the zeroconf data.
    #
    # Also find all neighbours
    routes, reverse_routes, neighbours = await hass.async_add_executor_job(
        _get_routes_and_neighbors
    )

    aiozc = await zeroconf.async_get_async_instance(hass)
    for data in async_read_zeroconf_cache(aiozc):
        if not data.extended_pan_id:
            continue

        network = networks.setdefault(
            data.extended_pan_id,
            {
                "name": data.network_name,
                "routers": {},
                "prefixes": set(),
                "unexpected_routers": set(),
            },
        )

        if not data.server:
            continue

        router = network["routers"][data.server] = {
            "server": data.server,
            "addresses": data.addresses or [],
            "neighbours": {},
            "thread_version": data.thread_version,
            "model": data.model_name,
            "vendor": data.vendor_name,
            "routes": {},
        }

        # For every address this border router hass, see if we have seen
        # it in the route table as a via - these are the routes its
        # announcing via RA
        if data.addresses:
            for address in data.addresses:
                if address in routes:
                    router["routes"].update(routes[address])

                if address in neighbours:
                    router["neighbours"][address] = neighbours[address]

        network["prefixes"].update(router["routes"].keys())

    # Find unexpected via's.
    # Collect all router addresses and then for each prefix, find via's that aren't
    # a known router for that prefix.
    for network in networks.values():
        routers = set()

        for router in network["routers"].values():
            routers.update(router["addresses"])

        for prefix in network["prefixes"]:
            if prefix not in reverse_routes:
                continue
            if ghosts := reverse_routes[prefix] - routers:
                network["unexpected_routers"] = ghosts

    return {
        "networks": networks,
    }