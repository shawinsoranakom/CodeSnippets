def create_time_server_exposures(
    xknx: XKNX,
    config: KNXTimeServerStoreModel,
) -> list[KnxExposeTime]:
    """Create exposures from UI config store time server config."""
    exposures: list[KnxExposeTime] = []
    device_cls: type[DateDevice | DateTimeDevice | TimeDevice]
    for expose_type, data in config.items():
        if not data or (ga := data.get("write")) is None:  # type: ignore[attr-defined]
            continue
        match expose_type:
            case "time":
                device_cls = TimeDevice
            case "date":
                device_cls = DateDevice
            case "datetime":
                device_cls = DateTimeDevice
            case _:
                continue
        exposures.append(
            KnxExposeTime(
                xknx=xknx,
                options=KnxExposeTimeOptions(
                    name=f"timeserver_{expose_type}",
                    group_address=parse_device_group_address(ga),
                    device_cls=device_cls,
                ),
            )
        )
    for exposure in exposures:
        exposure.async_register()
    return exposures