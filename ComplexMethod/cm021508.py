async def test_self_referencing_icon_with_no_loop(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test a self referencing icon that does not loop."""

    hass.states.async_set("sensor.heartworm_high_80", 10)
    hass.states.async_set("sensor.heartworm_low_57", 10)
    hass.states.async_set("sensor.heartworm_avg_64", 10)
    hass.states.async_set("sensor.heartworm_avg_57", 10)

    value_template_str = """{% if (states.sensor.heartworm_high_80.state|int >= 10) and (states.sensor.heartworm_low_57.state|int >= 10) %}
            extreme
          {% elif (states.sensor.heartworm_avg_64.state|int >= 30) %}
            high
          {% elif (states.sensor.heartworm_avg_64.state|int >= 14) %}
            moderate
          {% elif (states.sensor.heartworm_avg_64.state|int >= 5) %}
            slight
          {% elif (states.sensor.heartworm_avg_57.state|int >= 5) %}
            marginal
          {% elif (states.sensor.heartworm_avg_57.state|int < 5) %}
            none
          {% endif %}"""

    icon_template_str = """{% if is_state('sensor.heartworm_risk',"extreme") %}
            mdi:hazard-lights
          {% elif is_state('sensor.heartworm_risk',"high") %}
            mdi:triangle-outline
          {% elif is_state('sensor.heartworm_risk',"moderate") %}
            mdi:alert-circle-outline
          {% elif is_state('sensor.heartworm_risk',"slight") %}
            mdi:exclamation
          {% elif is_state('sensor.heartworm_risk',"marginal") %}
            mdi:heart
          {% elif is_state('sensor.heartworm_risk',"none") %}
            mdi:snowflake
          {% endif %}"""

    await async_setup_component(
        hass,
        template.DOMAIN,
        {
            "template": [
                {
                    "sensor": [
                        {
                            "name": "heartworm_risk",
                            "state": value_template_str,
                            "icon": icon_template_str,
                        }
                    ],
                }
            ]
        },
    )

    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 5

    hass.states.async_set("sensor.heartworm_high_80", 10)

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert "Template loop detected" not in caplog.text

    state = hass.states.get("sensor.heartworm_risk")
    assert state.state == "extreme"
    assert state.attributes[ATTR_ICON] == "mdi:hazard-lights"

    await hass.async_block_till_done()
    assert state.state == "extreme"
    assert state.attributes[ATTR_ICON] == "mdi:hazard-lights"
    assert "Template loop detected" not in caplog.text