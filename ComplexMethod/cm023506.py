def build_device_fixture(
    heat_pump: bool,
    mode_pending: bool,
    setpoint_pending: bool,
    has_vacation_mode: bool,
    supports_hot_water_plus: bool,
):
    """Build a fixture for a device."""
    supported_modes: list[SupportedOperationModeInfo] = [
        SupportedOperationModeInfo(
            mode=OperationMode.ELECTRIC,
            original_name="ELECTRIC",
            has_day_selection=True,
            supports_hot_water_plus=supports_hot_water_plus,
        ),
    ]

    if heat_pump:
        supported_modes.append(
            SupportedOperationModeInfo(
                mode=OperationMode.HYBRID,
                original_name="HYBRID",
                has_day_selection=False,
                supports_hot_water_plus=supports_hot_water_plus,
            )
        )
        supported_modes.append(
            SupportedOperationModeInfo(
                mode=OperationMode.HEAT_PUMP,
                original_name="HEAT_PUMP",
                has_day_selection=False,
                supports_hot_water_plus=supports_hot_water_plus,
            )
        )

    if has_vacation_mode:
        supported_modes.append(
            SupportedOperationModeInfo(
                mode=OperationMode.VACATION,
                original_name="VACATION",
                has_day_selection=True,
                supports_hot_water_plus=False,
            )
        )

    current_mode = OperationMode.HEAT_PUMP if heat_pump else OperationMode.ELECTRIC

    if heat_pump and supports_hot_water_plus:
        device_type = DeviceType.RE3_PREMIUM
    elif heat_pump:
        device_type = DeviceType.NEXT_GEN_HEAT_PUMP
    else:
        device_type = DeviceType.RE3_CONNECTED

    return Device(
        brand="aosmith",
        model="Example model",
        device_type=device_type,
        dsn="dsn",
        junction_id="junctionId",
        name="My water heater",
        serial="serial",
        install_location="Basement",
        supported_modes=supported_modes,
        supports_hot_water_plus=supports_hot_water_plus,
        status=DeviceStatus(
            firmware_version="2.14",
            is_online=True,
            current_mode=current_mode,
            mode_change_pending=mode_pending,
            temperature_setpoint=130,
            temperature_setpoint_pending=setpoint_pending,
            temperature_setpoint_previous=130,
            temperature_setpoint_maximum=130,
            hot_water_status=90,
            hot_water_plus_level=1 if supports_hot_water_plus else None,
        ),
    )