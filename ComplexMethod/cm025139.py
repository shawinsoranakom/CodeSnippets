async def test_label_areas(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    label_registry: lr.LabelRegistry,
) -> None:
    """Test label_areas function."""

    # Test non existing area ID
    info = render_to_info(hass, "{{ label_areas('deadbeef') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'deadbeef' | label_areas }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ label_areas(42) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 42 | label_areas }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Create an area with an label
    label = label_registry.async_create("Upstairs")
    master_bedroom = area_registry.async_create(
        "Master Bedroom", labels=[label.label_id]
    )

    # Get areas by label ID
    info = render_to_info(hass, f"{{{{ label_areas('{label.label_id}') }}}}")
    assert_result_info(info, [master_bedroom.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.label_id}' | label_areas }}}}")
    assert_result_info(info, [master_bedroom.id])
    assert info.rate_limit is None

    # Get areas by label name
    info = render_to_info(hass, f"{{{{ label_areas('{label.name}') }}}}")
    assert_result_info(info, [master_bedroom.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{label.name}' | label_areas }}}}")
    assert_result_info(info, [master_bedroom.id])
    assert info.rate_limit is None