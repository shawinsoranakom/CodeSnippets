async def test_eve_thermo_v5_presets(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test Eve Thermo v5 thermostat presets attributes and state updates."""
    # test entity attributes
    entity_id = "climate.eve_thermo_20ecd1701"
    state = hass.states.get(entity_id)
    assert state

    # test supported features correctly parsed
    mask = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.PRESET_MODE
    )
    assert state.attributes["supported_features"] & mask == mask

    # Test preset modes parsed correctly from Eve Thermo v5
    # Should use HA standard presets for known ones, original names for others
    # PRESET_NONE is always included to allow users to clear the preset
    assert state.attributes["preset_modes"] == [
        "home",
        "away",
        "sleep",
        "wake",
        "vacation",
        "going_to_sleep",
        "Eco",
        PRESET_NONE,
    ]
    assert state.attributes["preset_mode"] == "home"

    # Get presets from the node for dynamic testing
    presets_attribute = matter_node.endpoints[1].get_attribute_value(
        513,
        clusters.Thermostat.Attributes.Presets.attribute_id,
    )
    preset_by_name = {preset.name: preset.presetHandle for preset in presets_attribute}

    # test set_preset_mode with "home" preset (HA standard)
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "home",
        },
        blocking=True,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.Thermostat.Commands.SetActivePresetRequest(
            presetHandle=preset_by_name["Home"]
        ),
    )
    # Verify preset_mode is optimistically updated
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == "home"
    matter_client.send_device_command.reset_mock()

    # test set_preset_mode with "away" preset (HA standard)
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "away",
        },
        blocking=True,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.Thermostat.Commands.SetActivePresetRequest(
            presetHandle=preset_by_name["Away"]
        ),
    )
    # Verify preset_mode is optimistically updated
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == "away"
    matter_client.send_device_command.reset_mock()

    # test set_preset_mode with "eco" preset (custom, device-provided name)
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "Eco",
        },
        blocking=True,
    )
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.Thermostat.Commands.SetActivePresetRequest(
            presetHandle=preset_by_name["Eco"]
        ),
    )
    matter_client.send_device_command.reset_mock()

    # test set_preset_mode with invalid preset mode
    # The climate platform validates preset modes before calling our method

    # Get current state to derive expected modes
    state = hass.states.get(entity_id)
    assert state
    expected_modes = ", ".join(state.attributes["preset_modes"])

    with pytest.raises(ServiceValidationError) as err:
        await hass.services.async_call(
            "climate",
            "set_preset_mode",
            {
                "entity_id": entity_id,
                "preset_mode": "InvalidPreset",
            },
            blocking=True,
        )

    assert err.value.translation_key == "not_valid_preset_mode"
    assert err.value.translation_placeholders == {
        "mode": "InvalidPreset",
        "modes": expected_modes,
    }

    # Ensure no command was sent for invalid preset
    assert matter_client.send_device_command.call_count == 0
    # Test that preset_mode is updated when ActivePresetHandle is set from device
    set_node_attribute(
        matter_node,
        1,
        513,
        clusters.Thermostat.Attributes.ActivePresetHandle.attribute_id,
        preset_by_name["Home"],
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == "home"

    # Test that preset_mode is updated when ActivePresetHandle changes to different preset
    set_node_attribute(
        matter_node,
        1,
        513,
        clusters.Thermostat.Attributes.ActivePresetHandle.attribute_id,
        preset_by_name["Away"],
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == "away"

    # Test that preset_mode is PRESET_NONE when ActivePresetHandle is cleared
    set_node_attribute(
        matter_node,
        1,
        513,
        clusters.Thermostat.Attributes.ActivePresetHandle.attribute_id,
        None,
    )
    await trigger_subscription_callback(hass, matter_client)
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == PRESET_NONE

    # Test that users can set preset_mode to PRESET_NONE to clear the active preset
    matter_client.send_device_command.reset_mock()
    # First set a preset so we have something to clear
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "home",
        },
        blocking=True,
    )
    matter_client.send_device_command.reset_mock()

    # Now call set_preset_mode with PRESET_NONE to clear it
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": PRESET_NONE,
        },
        blocking=True,
    )

    # Verify the command was sent with null value to clear the preset
    assert matter_client.send_device_command.call_count == 1
    assert matter_client.send_device_command.call_args == call(
        node_id=matter_node.node_id,
        endpoint_id=1,
        command=clusters.Thermostat.Commands.SetActivePresetRequest(presetHandle=None),
    )
    # Verify preset_mode is optimistically updated to PRESET_NONE
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == PRESET_NONE