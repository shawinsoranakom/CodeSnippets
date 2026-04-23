def validate_child(
    gateway_id: GatewayId,
    gateway: BaseAsyncGateway,
    node_id: int,
    child: ChildSensor,
    value_type: int | None = None,
) -> defaultdict[Platform, list[DevId]]:
    """Validate a child. Returns a dict mapping hass platform names to list of DevId."""
    validated: defaultdict[Platform, list[DevId]] = defaultdict(list)
    presentation: type[IntEnum] = gateway.const.Presentation
    set_req: type[IntEnum] = gateway.const.SetReq
    child_type_name: SensorType | None = next(
        (member.name for member in presentation if member.value == child.type), None
    )
    if not child_type_name:
        _LOGGER.warning("Child type %s is not supported", child.type)
        return validated

    value_types: set[int] = {value_type} if value_type else {*child.values}
    value_type_names: set[ValueType] = {
        member.name for member in set_req if member.value in value_types
    }
    platforms: list[Platform] = TYPE_TO_PLATFORMS.get(child_type_name, [])
    if not platforms:
        _LOGGER.warning("Child type %s is not supported", child.type)
        return validated

    for platform in platforms:
        platform_v_names: set[ValueType] = FLAT_PLATFORM_TYPES[
            platform, child_type_name
        ]
        v_names: set[ValueType] = platform_v_names & value_type_names
        if not v_names:
            child_value_names: set[ValueType] = {
                member.name for member in set_req if member.value in child.values
            }
            v_names = platform_v_names & child_value_names

        for v_name in v_names:
            child_schema_gen = SCHEMAS.get((platform, v_name), default_schema)
            child_schema = child_schema_gen(gateway, child, v_name)
            try:
                child_schema(child.values)
            except vol.Invalid as exc:
                _LOGGER.warning(
                    "Invalid %s on node %s, %s platform: %s",
                    child,
                    node_id,
                    platform,
                    exc,
                )
                continue
            dev_id: DevId = (
                gateway_id,
                node_id,
                child.id,
                set_req[v_name].value,
            )
            validated[platform].append(dev_id)

    return validated