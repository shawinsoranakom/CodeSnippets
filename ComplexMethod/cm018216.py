async def test_get_services_for_target_caching(
    mock_has_services: Mock,
    mock_load_yaml: Mock,
    hass: HomeAssistant,
    websocket_client: MockHAClientWebSocket,
) -> None:
    """Test that flattened service descriptions are cached and reused."""

    def get_common_service_descriptions(domain: str):
        return f"""
        turn_on:
          target:
            entity:
              domain: {domain}
        """

    def _load_yaml(fname, secrets=None):
        domain = fname.split("/")[-2]
        with io.StringIO(get_common_service_descriptions(domain)) as file:
            return parse_yaml(file)

    mock_load_yaml.side_effect = _load_yaml
    await hass.async_block_till_done()

    hass.services.async_register("light", "turn_on", lambda call: None)
    hass.services.async_register("switch", "turn_on", lambda call: None)
    await hass.async_block_till_done()

    async def call_command():
        await websocket_client.send_json_auto_id(
            {
                "type": "get_services_for_target",
                "target": {"entity_id": ["light.test1"]},
            }
        )
        msg = await websocket_client.receive_json()
        assert msg["success"]

    with patch(
        "homeassistant.components.websocket_api.automation._async_get_automation_components_for_target",
        return_value=set(),
    ) as mock_get_components:
        # First call: should create and cache flat descriptions
        await call_command()

        assert mock_get_components.call_count == 1
        first_flat_descriptions = mock_get_components.call_args_list[0][0][4]
        assert first_flat_descriptions == {
            "light.turn_on": {
                "fields": {},
                "target": {"entity": [{"domain": ["light"]}]},
            },
            "switch.turn_on": {
                "fields": {},
                "target": {"entity": [{"domain": ["switch"]}]},
            },
        }

        # Second call: should reuse cached flat descriptions
        await call_command()
        assert mock_get_components.call_count == 2
        second_flat_descriptions = mock_get_components.call_args_list[1][0][4]
        assert first_flat_descriptions is second_flat_descriptions

        # Register a new service to invalidate cache
        hass.services.async_register("new_domain", "new_service", lambda call: None)
        await hass.async_block_till_done()

        # Third call: cache should be rebuilt
        await call_command()
        assert mock_get_components.call_count == 3
        third_flat_descriptions = mock_get_components.call_args_list[2][0][4]
        assert "new_domain.new_service" in third_flat_descriptions
        assert third_flat_descriptions is not first_flat_descriptions