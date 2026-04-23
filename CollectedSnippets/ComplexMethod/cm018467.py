async def test_blu_trv_stale_device_removal(
    hass: HomeAssistant,
    mock_blu_trv: Mock,
    entity_registry: EntityRegistry,
    device_registry: DeviceRegistry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test BLU TRV removal of stale a device after un-pairing."""
    trv_200_entity_id = "climate.trv_name"
    trv_201_entity_id = "climate.trv_201"

    monkeypatch.setattr(mock_blu_trv, "model", MODEL_BLU_GATEWAY_G3)
    gw_entry = await init_integration(hass, 3, model=MODEL_BLU_GATEWAY_G3)

    # verify that both trv devices are present
    assert hass.states.get(trv_200_entity_id) is not None
    trv_200_entry = entity_registry.async_get(trv_200_entity_id)
    assert trv_200_entry

    trv_200_device_entry = device_registry.async_get(trv_200_entry.device_id)
    assert trv_200_device_entry
    assert trv_200_device_entry.name == "TRV-Name"

    assert hass.states.get(trv_201_entity_id) is not None
    trv_201_entry = entity_registry.async_get(trv_201_entity_id)
    assert trv_201_entry

    trv_201_device_entry = device_registry.async_get(trv_201_entry.device_id)
    assert trv_201_device_entry
    assert trv_201_device_entry.name == "TRV-201"

    # simulate un-pairing of trv 201 device
    monkeypatch.delitem(mock_blu_trv.config, "blutrv:201")
    monkeypatch.delitem(mock_blu_trv.status, "blutrv:201")

    await hass.config_entries.async_reload(gw_entry.entry_id)
    await hass.async_block_till_done()

    # verify that trv 201 is removed
    assert hass.states.get(trv_200_entity_id) is not None
    assert device_registry.async_get(trv_200_entry.device_id) is not None

    assert hass.states.get(trv_201_entity_id) is None
    assert device_registry.async_get(trv_201_entry.device_id) is None