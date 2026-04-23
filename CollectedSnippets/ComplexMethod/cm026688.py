async def validate_input(hass: HomeAssistant, address: str) -> Error | None:
    """Return error if cannot connect and validate."""

    ble_device = async_ble_device_from_address(hass, address.upper(), connectable=True)

    if ble_device is None:
        count_scanners = async_scanner_count(hass, connectable=True)
        _LOGGER.debug("Count of BLE scanners in HA bt: %i", count_scanners)

        if count_scanners < 1:
            return Error.NO_SCANNERS
        return Error.NOT_FOUND

    try:
        light = HueBleLight(ble_device)
        await light.connect()
        get_available_color_modes(light)
        await light.poll_state()

    except ConnectionError as e:
        _LOGGER.exception("Error connecting to light")
        return (
            Error.INVALID_AUTH
            if type(e.__cause__) is PairingError
            else Error.CANNOT_CONNECT
        )
    except HueBleError:
        _LOGGER.exception("Unexpected error validating light connection")
        return Error.UNKNOWN
    except HomeAssistantError:
        return Error.NOT_SUPPORTED
    else:
        return None
    finally:
        await light.disconnect()