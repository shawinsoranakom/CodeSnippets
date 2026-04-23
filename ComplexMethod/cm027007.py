def _setup_keypad(
    hass: HomeAssistant,
    entry_data: LutronData,
    keypad: Keypad,
    area_name: str,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Set up a Lutron keypad."""

    _async_check_keypad_identifiers(
        hass,
        device_registry,
        keypad.id,
        keypad.uuid,
        keypad.legacy_uuid,
        entry_data.client.guid,
    )
    leds_by_number = {led.number: led for led in keypad.leds}
    for button in keypad.buttons:
        # If the button has a function assigned to it, add it as a scene
        if button.name != "Unknown Button" and button.button_type in (
            "SingleAction",
            "Toggle",
            "SingleSceneRaiseLower",
            "MasterRaiseLower",
            "AdvancedToggle",
        ):
            # Associate an LED with a button if there is one
            led = leds_by_number.get(button.number)
            entry_data.scenes.append((area_name, keypad, button, led))

            _async_check_entity_unique_id(
                hass,
                entity_registry,
                Platform.SCENE,
                button.uuid,
                button.legacy_uuid,
                entry_data.client.guid,
            )
            if led is not None:
                for platform in (Platform.SWITCH, Platform.SELECT):
                    _async_check_entity_unique_id(
                        hass,
                        entity_registry,
                        platform,
                        led.uuid,
                        led.legacy_uuid,
                        entry_data.client.guid,
                    )
        if button.button_type:
            entry_data.buttons.append((area_name, keypad, button))