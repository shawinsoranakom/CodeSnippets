async def make_device_data(
    hass: HomeAssistant,
    entry: SwitchbotCloudConfigEntry,
    api: SwitchBotAPI,
    device: Device | Remote,
    devices_data: SwitchbotDevices,
    coordinators_by_id: dict[str, SwitchBotCoordinator],
) -> None:
    """Make device data."""
    if isinstance(device, Remote) and device.device_type.endswith("Air Conditioner"):
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.climates.append((device, coordinator))

    if (
        isinstance(device, Remote | Device)
        and device.device_type == "Smart Radiator Thermostat"
    ):
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.climates.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))

    if (
        isinstance(device, Device)
        and (
            device.device_type.startswith("Plug")
            or device.device_type in ["Relay Switch 1PM", "Relay Switch 1"]
        )
    ) or isinstance(device, Remote):
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.switches.append((device, coordinator))

    if isinstance(device, Device) and device.device_type in [
        "Meter",
        "MeterPlus",
        "WoIOSensor",
        "Hub 2",
        "MeterPro",
        "MeterPro(CO2)",
        "Relay Switch 1PM",
        "Plug Mini (US)",
        "Plug Mini (JP)",
        "Plug Mini (EU)",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type in [
        "K10+",
        "K10+ Pro",
        "Robot Vacuum Cleaner S1",
        "Robot Vacuum Cleaner S1 Plus",
        "K20+ Pro",
        "Robot Vacuum Cleaner K10+ Pro Combo",
        "Robot Vacuum Cleaner S10",
        "Robot Vacuum Cleaner S20",
        "S20",
        "Robot Vacuum Cleaner K11 Plus",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id, True
        )
        devices_data.vacuums.append((device, coordinator))

    if isinstance(device, Device) and device.device_type in [
        "Smart Lock",
        "Smart Lock Lite",
        "Smart Lock Pro",
        "Smart Lock Ultra",
        "Smart Lock Vision",
        "Smart Lock Vision Pro",
        "Smart Lock Pro Wifi",
        "Lock Vision",
        "Lock Vision Pro",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.locks.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))
        devices_data.binary_sensors.append((device, coordinator))

    if isinstance(device, Device) and device.device_type == "Bot":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id, True
        )
        devices_data.sensors.append((device, coordinator))
        if coordinator.data is not None:
            if coordinator.data.get("deviceMode") == "pressMode":
                devices_data.buttons.append((device, coordinator))
            else:
                devices_data.switches.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "Relay Switch 2PM":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.sensors.append((device, coordinator))
        devices_data.switches.append((device, coordinator))

    if isinstance(device, Device) and device.device_type.startswith("Air Purifier"):
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.fans.append((device, coordinator))
    if isinstance(device, Device) and device.device_type in [
        "Motion Sensor",
        "Contact Sensor",
        "Presence Sensor",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id, True
        )
        devices_data.sensors.append((device, coordinator))
        devices_data.binary_sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "Hub 3":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id, True
        )
        devices_data.sensors.append((device, coordinator))
        devices_data.binary_sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "Water Detector":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id, True
        )
        devices_data.binary_sensors.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))

    if isinstance(device, Device) and device.device_type in [
        "Battery Circulator Fan",
        "Standing Fan",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.fans.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "Circulator Fan":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.fans.append((device, coordinator))
    if isinstance(device, Device) and device.device_type in [
        "Curtain",
        "Curtain3",
        "Roller Shade",
        "Blind Tilt",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.covers.append((device, coordinator))
        devices_data.binary_sensors.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))

    if isinstance(device, Device) and device.device_type == "Garage Door Opener":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.covers.append((device, coordinator))
        devices_data.binary_sensors.append((device, coordinator))

    if isinstance(device, Device) and device.device_type in [
        "Strip Light",
        "Strip Light 3",
        "Floor Lamp",
        "Color Bulb",
        "RGBICWW Floor Lamp",
        "RGBICWW Strip Light",
        "Ceiling Light",
        "Ceiling Light Pro",
        "RGBIC Neon Rope Light",
        "RGBIC Neon Wire Rope Light",
        "Candle Warmer Lamp",
    ]:
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.lights.append((device, coordinator))

    if isinstance(device, Device) and device.device_type == "Humidifier2":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.humidifiers.append((device, coordinator))

    if isinstance(device, Device) and device.device_type == "Humidifier":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.humidifiers.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "Climate Panel":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.binary_sensors.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "AI Art Frame":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.buttons.append((device, coordinator))
        devices_data.sensors.append((device, coordinator))
        devices_data.images.append((device, coordinator))
    if isinstance(device, Device) and device.device_type == "WeatherStation":
        coordinator = await coordinator_for_device(
            hass, entry, api, device, coordinators_by_id
        )
        devices_data.sensors.append((device, coordinator))