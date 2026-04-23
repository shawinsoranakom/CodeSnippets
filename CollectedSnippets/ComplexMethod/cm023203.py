async def test_energy_production_sensors(
    hass: HomeAssistant, energy_production, client, integration
) -> None:
    """Test sensors for Energy Production CC."""
    for entity_id_suffix, state_data in ENERGY_PRODUCTION_ENTITY_MAP.items():
        state = hass.states.get(f"sensor.node_2_{entity_id_suffix}")
        assert state
        assert state.state == str(state_data["state"])
        for attr, val in state_data["attributes"].items():
            assert state.attributes[attr] == val

        for attr in state_data.get("missing_attributes", []):
            assert attr not in state.attributes