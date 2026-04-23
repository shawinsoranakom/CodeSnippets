async def test_floor_areas(
    hass: HomeAssistant,
    floor_registry: fr.FloorRegistry,
    area_registry: ar.AreaRegistry,
) -> None:
    """Test floor_areas function."""

    # Test non existing floor ID
    info = render_to_info(hass, "{{ floor_areas('skyring') }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 'skyring' | floor_areas }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    # Test wrong value type
    info = render_to_info(hass, "{{ floor_areas(42) }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    info = render_to_info(hass, "{{ 42 | floor_areas }}")
    assert_result_info(info, [])
    assert info.rate_limit is None

    floor = floor_registry.async_create("First floor")
    area = area_registry.async_create("Living room")
    area_registry.async_update(area.id, floor_id=floor.floor_id)

    # Get areas by floor ID
    info = render_to_info(hass, f"{{{{ floor_areas('{floor.floor_id}') }}}}")
    assert_result_info(info, [area.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{floor.floor_id}' | floor_areas }}}}")
    assert_result_info(info, [area.id])
    assert info.rate_limit is None

    # Get areas by floor name
    info = render_to_info(hass, f"{{{{ floor_areas('{floor.name}') }}}}")
    assert_result_info(info, [area.id])
    assert info.rate_limit is None

    info = render_to_info(hass, f"{{{{ '{floor.name}' | floor_areas }}}}")
    assert_result_info(info, [area.id])
    assert info.rate_limit is None