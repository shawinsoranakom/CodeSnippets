async def test_update_remove_key_script_config(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_config_store: dict[str, Any],
) -> None:
    """Test updating script config while removing a key."""
    with patch.object(config, "SECTIONS", [script]):
        await async_setup_component(hass, "config", {})

    assert sorted(hass.states.async_entity_ids("script")) == []

    client = await hass_client()

    orig_data = {"sun": {"key": "value"}, "moon": {"key": "value"}}
    hass_config_store["scripts.yaml"] = orig_data

    resp = await client.post(
        "/api/config/script/config/moon",
        data=json.dumps({"sequence": []}),
    )
    await hass.async_block_till_done()
    assert sorted(hass.states.async_entity_ids("script")) == [
        "script.moon",
        "script.sun",
    ]
    assert hass.states.get("script.moon").state == STATE_OFF
    assert hass.states.get("script.sun").state == STATE_UNAVAILABLE

    assert resp.status == HTTPStatus.OK
    result = await resp.json()
    assert result == {"result": "ok"}

    new_data = hass_config_store["scripts.yaml"]
    assert list(new_data["moon"]) == ["sequence"]
    assert new_data["moon"] == {"sequence": []}