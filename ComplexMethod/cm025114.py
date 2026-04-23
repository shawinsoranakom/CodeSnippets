async def test_device_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test device_entities function."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing device ids
    info = render_to_info(hass, "{{ device_entities('abc123') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ device_entities(56) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test device without entities
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    info = render_to_info(hass, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test device with single entity, which has no state
    entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    info = render_to_info(hass, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, ["light.hue_5678"], [])
    assert info.rate_limit is None
    info = render_to_info(
        hass,
        (
            f"{{{{ device_entities('{device_entry.id}') | expand "
            "| sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}"
        ),
    )
    assert_result_info(info, "", ["light.hue_5678"])
    assert info.rate_limit is None

    # Test device with single entity, with state
    hass.states.async_set("light.hue_5678", "happy")
    info = render_to_info(
        hass,
        (
            f"{{{{ device_entities('{device_entry.id}') | expand "
            "| sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}"
        ),
    )
    assert_result_info(info, "light.hue_5678", ["light.hue_5678"])
    assert info.rate_limit is None

    # Test device with multiple entities, which have a state
    entity_registry.async_get_or_create(
        "light",
        "hue",
        "ABCD",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    hass.states.async_set("light.hue_abcd", "camper")
    info = render_to_info(hass, f"{{{{ device_entities('{device_entry.id}') }}}}")
    assert_result_info(info, ["light.hue_5678", "light.hue_abcd"], [])
    assert info.rate_limit is None
    info = render_to_info(
        hass,
        (
            f"{{{{ device_entities('{device_entry.id}') | expand "
            "| sort(attribute='entity_id') | map(attribute='entity_id') | join(', ') }}"
        ),
    )
    assert_result_info(
        info, "light.hue_5678, light.hue_abcd", ["light.hue_5678", "light.hue_abcd"]
    )
    assert info.rate_limit is None