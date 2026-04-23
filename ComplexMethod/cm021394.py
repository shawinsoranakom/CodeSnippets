async def test_reauth_flow(hass: HomeAssistant, mock_list_contracts) -> None:
    """Test a reauthentication flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="12345",
        data={
            "username": "test-username",
            "password": "test-password",
            "country": "PT",
        },
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.prosegur.config_flow.Installation.list",
            return_value=mock_list_contracts,
        ) as mock_installation,
        patch(
            "homeassistant.components.prosegur.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "new_password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data == {
        "country": "PT",
        "username": "test-username",
        "password": "new_password",
    }

    assert len(mock_installation.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1