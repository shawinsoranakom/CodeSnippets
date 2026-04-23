def _handle_energy_sensor_interface(
    hap: HomematicipHAP, device: Device
) -> list[HomematicipGenericEntity]:
    """Handle energy sensor interface devices."""
    result: list[HomematicipGenericEntity] = []
    for ch in get_channels_from_device(
        device, FunctionalChannelType.ENERGY_SENSORS_INTERFACE_CHANNEL
    ):
        if ch.connectedEnergySensorType == ESI_CONNECTED_SENSOR_TYPE_IEC:
            if ch.currentPowerConsumption is not None:
                result.append(HmipEsiIecPowerConsumption(hap, device))
            if ch.energyCounterOneType != ESI_TYPE_UNKNOWN:
                result.append(HmipEsiIecEnergyCounterHighTariff(hap, device))
            if ch.energyCounterTwoType != ESI_TYPE_UNKNOWN:
                result.append(HmipEsiIecEnergyCounterLowTariff(hap, device))
            if ch.energyCounterThreeType != ESI_TYPE_UNKNOWN:
                result.append(HmipEsiIecEnergyCounterInputSingleTariff(hap, device))

        if ch.connectedEnergySensorType == ESI_CONNECTED_SENSOR_TYPE_GAS:
            if ch.currentGasFlow is not None:
                result.append(HmipEsiGasCurrentGasFlow(hap, device))
            if ch.gasVolume is not None:
                result.append(HmipEsiGasGasVolume(hap, device))

        if ch.connectedEnergySensorType == ESI_CONNECTED_SENSOR_TYPE_LED:
            if ch.currentPowerConsumption is not None:
                result.append(HmipEsiLedCurrentPowerConsumption(hap, device))
            result.append(HmipEsiLedEnergyCounterHighTariff(hap, device))

    return result