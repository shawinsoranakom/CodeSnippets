async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        title="test-username",
        domain=DOMAIN,
        unique_id="test-username",
        data={
            "username": "test-username",
            "password": "test-password",
            "area_id": "1",
        },
        version=2,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.yale_smart_alarm.config_flow.YaleSmartAlarmClient",
        ) as mock_yale,
        patch(
            "homeassistant.components.yale_smart_alarm.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "password": "new-test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data == {
        "username": "test-username",
        "password": "new-test-password",
        "area_id": "1",
    }

    assert len(mock_yale.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1