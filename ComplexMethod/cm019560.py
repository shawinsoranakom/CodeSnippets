async def test_preset_mode_with_unnamed_preset(
    hass: HomeAssistant,
    matter_client: MagicMock,
    matter_node: MatterNode,
) -> None:
    """Test preset mode when a preset has no name or empty name.

    This tests the fallback preset naming case where a preset does not have
    a mapped presetScenario and also has no device-provided name, requiring
    the fallback Preset{i} naming pattern.
    """
    entity_id = "climate.eve_thermo_20ecd1701"

    # Get current presets from the node
    presets_attribute = matter_node.endpoints[1].get_attribute_value(
        513,
        clusters.Thermostat.Attributes.Presets.attribute_id,
    )

    assert presets_attribute is not None

    # Add a new preset with unmapped scenario (e.g., 255) and no name
    new_preset = clusters.Thermostat.Structs.PresetStruct(
        presetHandle=b"\xff",
        presetScenario=255,  # Unmapped scenario
        name="",  # Empty name
    )
    presets_attribute.append(new_preset)

    # Update the node with the new preset list
    set_node_attribute(
        matter_node,
        1,
        513,
        clusters.Thermostat.Attributes.Presets.attribute_id,
        presets_attribute,
    )

    # Trigger subscription callback to update entity
    await trigger_subscription_callback(hass, matter_client)

    # Verify the preset was added with the fallback name "Preset8"
    state = hass.states.get(entity_id)
    assert state
    assert "Preset8" in state.attributes["preset_modes"]

    # Test that the unnamed preset can be set as active
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {
            "entity_id": entity_id,
            "preset_mode": "Preset8",
        },
        blocking=True,
    )
    state = hass.states.get(entity_id)
    assert state
    assert state.attributes["preset_mode"] == "Preset8"

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