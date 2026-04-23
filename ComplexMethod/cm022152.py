async def test_bluetooth_flow_errors(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    patch_target: str,
    side_effect: Exception,
    expected_error: dict,
) -> None:
    """Test we can handle a bluetooth discovery flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_BLUETOOTH},
        data=FAKE_SERVICE_INFO,
    )

    with patch(
        f"homeassistant.components.eurotronic_cometblue.config_flow.AsyncCometBlue.{patch_target}",
        side_effect=side_effect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_USER_INPUT,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] == expected_error

    # now retry without side effect, simulating a user correcting the issue (e.g. entering correct PIN)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        FIXTURE_USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].title == f"{FIXTURE_DEVICE_NAME} {FIXTURE_MAC}"
    assert result["result"].unique_id == FIXTURE_MAC
    assert result["result"].data == {
        CONF_ADDRESS: FIXTURE_MAC,
        CONF_PIN: FIXTURE_USER_INPUT[CONF_PIN],
    }
    assert len(mock_setup_entry.mock_calls) == 1