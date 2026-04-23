async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: HomematicIPConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the HomematicIP Cloud binary sensor from a config entry."""
    hap = config_entry.runtime_data
    entities: list[HomematicipGenericEntity] = [HomematicipCloudConnectionSensor(hap)]
    for device in hap.home.devices:
        if isinstance(device, AccelerationSensor):
            entities.append(HomematicipAccelerationSensor(hap, device))
        if isinstance(device, TiltVibrationSensor):
            entities.append(HomematicipTiltVibrationSensor(hap, device))
        if isinstance(device, WiredInput32):
            entities.extend(
                HomematicipMultiContactInterface(
                    hap, device, channel_real_index=channel.index
                )
                for channel in device.functionalChannels
                if isinstance(channel, MultiModeInputChannel)
            )
        elif isinstance(device, FullFlushContactInterface6):
            entities.extend(
                HomematicipMultiContactInterface(hap, device, channel=channel)
                for channel in range(1, 7)
            )
        elif isinstance(device, (ContactInterface, FullFlushContactInterface)):
            entities.append(HomematicipContactInterface(hap, device))
        if isinstance(
            device,
            (ShutterContact, ShutterContactMagnetic),
        ):
            entities.append(HomematicipShutterContact(hap, device))
        if isinstance(device, RotaryHandleSensor):
            entities.append(HomematicipShutterContact(hap, device, True))
        if isinstance(
            device,
            (
                MotionDetectorIndoor,
                MotionDetectorOutdoor,
                MotionDetectorPushButton,
            ),
        ):
            entities.append(HomematicipMotionDetector(hap, device))
        if isinstance(device, PluggableMainsFailureSurveillance):
            entities.append(
                HomematicipPluggableMainsFailureSurveillanceSensor(hap, device)
            )
        if _is_full_flush_lock_controller(device):
            entities.append(HomematicipFullFlushLockControllerLocked(hap, device))
            entities.append(HomematicipFullFlushLockControllerGlassBreak(hap, device))
        if isinstance(device, PresenceDetectorIndoor):
            entities.append(HomematicipPresenceDetector(hap, device))
        if isinstance(device, SmokeDetector):
            entities.append(HomematicipSmokeDetector(hap, device))
            if smoke_detector_channel_data_exists(device, "chamberDegraded"):
                entities.append(HomematicipSmokeDetectorChamberDegraded(hap, device))
        if isinstance(device, WaterSensor):
            entities.append(HomematicipWaterDetector(hap, device))
        if isinstance(device, (RainSensor, WeatherSensorPlus, WeatherSensorPro)):
            entities.append(HomematicipRainSensor(hap, device))
        if isinstance(device, (WeatherSensor, WeatherSensorPlus, WeatherSensorPro)):
            entities.append(HomematicipStormSensor(hap, device))
            entities.append(HomematicipSunshineSensor(hap, device))
        if isinstance(device, Device) and device.lowBat is not None:
            entities.append(HomematicipBatterySensor(hap, device))

    for group in hap.home.groups:
        if isinstance(group, SecurityGroup):
            entities.append(HomematicipSecuritySensorGroup(hap, device=group))
        elif isinstance(group, SecurityZoneGroup):
            entities.append(HomematicipSecurityZoneSensorGroup(hap, device=group))

    async_add_entities(entities)