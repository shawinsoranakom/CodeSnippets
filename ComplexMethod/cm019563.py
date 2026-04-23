async def test_label_modified_entity_translation_key(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test that label-modified entities have a translation key and a label postfix.

    When a device uses Matter labels to differentiate endpoints,
    the entity name gets the label as a postfix. The translation key
    must still always be set for translations.
    """
    # Top outlet
    entry_top = entity_registry.async_get("switch.eve_energy_20ecn4101_switch_top")
    assert entry_top is not None
    assert entry_top.translation_key == "switch"
    assert entry_top.original_name == "Switch (top)"

    state_top = hass.states.get("switch.eve_energy_20ecn4101_switch_top")
    assert state_top is not None
    assert state_top.name == "Eve Energy 20ECN4101 Switch (top)"

    # Bottom outlet
    entry_bottom = entity_registry.async_get(
        "switch.eve_energy_20ecn4101_switch_bottom"
    )
    assert entry_bottom is not None
    assert entry_bottom.translation_key == "switch"
    assert entry_bottom.original_name == "Switch (bottom)"

    state_bottom = hass.states.get("switch.eve_energy_20ecn4101_switch_bottom")
    assert state_bottom is not None
    assert state_bottom.name == "Eve Energy 20ECN4101 Switch (bottom)"