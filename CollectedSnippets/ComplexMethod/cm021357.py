async def test_insight_state_attributes(hass: HomeAssistant, pywemo_registry) -> None:
    """Verify the switch attributes are set for the Insight device."""
    await async_setup_component(hass, HA_DOMAIN, {})
    with create_pywemo_device(pywemo_registry, "Insight") as insight:
        wemo_entity = await async_create_wemo_entity(hass, insight, "")
        attributes = hass.states.get(wemo_entity.entity_id).attributes
        assert attributes[ATTR_ON_LATEST_TIME] == "00d 00h 20m 34s"
        assert attributes[ATTR_ON_TODAY_TIME] == "00d 01h 34m 38s"
        assert attributes[ATTR_ON_TOTAL_TIME] == "00d 02h 30m 12s"
        assert attributes[ATTR_POWER_THRESHOLD] == MOCK_INSIGHT_STATE_THRESHOLD_POWER
        assert attributes[ATTR_CURRENT_STATE_DETAIL] == STATE_OFF

        async def async_update():
            await hass.services.async_call(
                HA_DOMAIN,
                SERVICE_UPDATE_ENTITY,
                {ATTR_ENTITY_ID: [wemo_entity.entity_id]},
                blocking=True,
            )

        # Test 'ON' state detail value.
        insight.standby_state = pywemo.StandbyState.ON
        await async_update()
        attributes = hass.states.get(wemo_entity.entity_id).attributes
        assert attributes[ATTR_CURRENT_STATE_DETAIL] == STATE_ON

        # Test 'STANDBY' state detail value.
        insight.standby_state = pywemo.StandbyState.STANDBY
        await async_update()
        attributes = hass.states.get(wemo_entity.entity_id).attributes
        assert attributes[ATTR_CURRENT_STATE_DETAIL] == STATE_STANDBY

        # Test 'UNKNOWN' state detail value.
        insight.standby_state = None
        await async_update()
        attributes = hass.states.get(wemo_entity.entity_id).attributes
        assert attributes[ATTR_CURRENT_STATE_DETAIL] == STATE_UNKNOWN