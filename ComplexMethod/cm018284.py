async def test_airzone_create_selects(hass: HomeAssistant) -> None:
    """Test creation of selects."""

    await async_init_integration(hass)

    # Systems
    state = hass.states.get("select.system_1_q_adapt")
    assert state.state == "standard"

    # Zones
    state = hass.states.get("select.despacho_cold_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.despacho_heat_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.despacho_mode")
    assert state is None

    state = hass.states.get("select.despacho_sleep")
    assert state.state == "off"

    state = hass.states.get("select.dorm_1_cold_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.dorm_1_heat_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.dorm_1_mode")
    assert state is None

    state = hass.states.get("select.dorm_1_sleep")
    assert state.state == "off"

    state = hass.states.get("select.dorm_2_cold_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.dorm_2_heat_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.dorm_2_mode")
    assert state is None

    state = hass.states.get("select.dorm_2_sleep")
    assert state.state == "off"

    state = hass.states.get("select.dorm_ppal_cold_angle")
    assert state.state == "45deg"

    state = hass.states.get("select.dorm_ppal_heat_angle")
    assert state.state == "50deg"

    state = hass.states.get("select.dorm_ppal_mode")
    assert state is None

    state = hass.states.get("select.dorm_ppal_sleep")
    assert state.state == "30m"

    state = hass.states.get("select.salon_cold_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.salon_heat_angle")
    assert state.state == "90deg"

    state = hass.states.get("select.salon_mode")
    assert state.state == "heat"
    assert state.attributes.get(ATTR_OPTIONS) == [
        "cool",
        "dry",
        "fan",
        "heat",
        "stop",
    ]

    state = hass.states.get("select.salon_sleep")
    assert state.state == "off"