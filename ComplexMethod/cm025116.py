async def test_device_attr(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test device_attr and is_device_attr functions."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing device ids (device_attr)
    info = render_to_info(hass, "{{ device_attr('abc123', 'id') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ device_attr(56, 'id') }}")
    with pytest.raises(TemplateError):
        assert_result_info(info, None)

    # Test non existing device ids (is_device_attr)
    info = render_to_info(hass, "{{ is_device_attr('abc123', 'id', 'test') }}")
    assert_result_info(info, False)
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ is_device_attr(56, 'id', 'test') }}")
    with pytest.raises(TemplateError):
        assert_result_info(info, False)

    # Test non existing entity id (device_attr)
    info = render_to_info(hass, "{{ device_attr('entity.test', 'id') }}")
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existing entity id (is_device_attr)
    info = render_to_info(hass, "{{ is_device_attr('entity.test', 'id', 'test') }}")
    assert_result_info(info, False)
    assert info.rate_limit is None

    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        model="test",
    )
    entity_entry = entity_registry.async_get_or_create(
        "sensor", "test", "test", suggested_object_id="test", device_id=device_entry.id
    )

    # Test non existent device attribute (device_attr)
    info = render_to_info(
        hass, f"{{{{ device_attr('{device_entry.id}', 'invalid_attr') }}}}"
    )
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test non existent device attribute (is_device_attr)
    info = render_to_info(
        hass, f"{{{{ is_device_attr('{device_entry.id}', 'invalid_attr', 'test') }}}}"
    )
    assert_result_info(info, False)
    assert info.rate_limit is None

    # Test None device attribute (device_attr)
    info = render_to_info(
        hass, f"{{{{ device_attr('{device_entry.id}', 'manufacturer') }}}}"
    )
    assert_result_info(info, None)
    assert info.rate_limit is None

    # Test None device attribute mismatch (is_device_attr)
    info = render_to_info(
        hass, f"{{{{ is_device_attr('{device_entry.id}', 'manufacturer', 'test') }}}}"
    )
    assert_result_info(info, False)
    assert info.rate_limit is None

    # Test None device attribute match (is_device_attr)
    info = render_to_info(
        hass, f"{{{{ is_device_attr('{device_entry.id}', 'manufacturer', None) }}}}"
    )
    assert_result_info(info, True)
    assert info.rate_limit is None

    # Test valid device attribute match (device_attr)
    info = render_to_info(hass, f"{{{{ device_attr('{device_entry.id}', 'model') }}}}")
    assert_result_info(info, "test")
    assert info.rate_limit is None

    # Test valid device attribute match (device_attr)
    info = render_to_info(
        hass, f"{{{{ device_attr('{entity_entry.entity_id}', 'model') }}}}"
    )
    assert_result_info(info, "test")
    assert info.rate_limit is None

    # Test valid device attribute mismatch (is_device_attr)
    info = render_to_info(
        hass, f"{{{{ is_device_attr('{device_entry.id}', 'model', 'fail') }}}}"
    )
    assert_result_info(info, False)
    assert info.rate_limit is None

    # Test valid device attribute match (is_device_attr)
    info = render_to_info(
        hass, f"{{{{ is_device_attr('{device_entry.id}', 'model', 'test') }}}}"
    )
    assert_result_info(info, True)
    assert info.rate_limit is None

    # Test filter syntax (device_attr)
    info = render_to_info(
        hass, f"{{{{ '{entity_entry.entity_id}' | device_attr('model') }}}}"
    )
    assert_result_info(info, "test")
    assert info.rate_limit is None

    # Test test syntax (is_device_attr)
    info = render_to_info(
        hass,
        (
            f"{{{{ ['{device_entry.id}'] | select('is_device_attr', 'model', 'test') "
            "| list }}"
        ),
    )
    assert_result_info(info, [device_entry.id])
    assert info.rate_limit is None