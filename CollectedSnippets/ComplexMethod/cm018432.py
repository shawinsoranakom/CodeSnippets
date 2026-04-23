def test_device_classes_aligned() -> None:
    """Make sure all sensor device classes are also available in NumberDeviceClass."""

    for device_class in SensorDeviceClass:
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue

        assert hasattr(NumberDeviceClass, device_class.name)
        assert getattr(NumberDeviceClass, device_class.name).value == device_class.value

    for device_class, unit in SENSOR_DEVICE_CLASS_UNITS.items():
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue
        assert unit == NUMBER_DEVICE_CLASS_UNITS[device_class]