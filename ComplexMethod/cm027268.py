def skip_entity(model: str, device_point: DevicePoint) -> bool:
    """Check if entity should be skipped for this device model."""
    if device_point.parameter_id == "65535":
        # Garbage entity showing up on several firmware versions
        return True
    if model == "SMO 20":
        if (
            len(device_point.smart_home_categories) > 0
            or device_point.parameter_id in PARAMETER_ID_TO_INCLUDE_SMO20
        ):
            return False
        return True
    if model.lower().startswith("f"):
        # Entity names containing weekdays are used for advanced scheduling in the
        # heat pump and should not be exposed in the integration
        if any(d in device_point.parameter_name.lower() for d in WEEKDAYS):
            return True
        if device_point.parameter_id in PARAMETER_ID_TO_EXCLUDE_F730:
            return True
    return False