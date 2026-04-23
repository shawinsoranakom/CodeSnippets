async def test_user_create_entry(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, snapshot: SnapshotAssertion
) -> None:
    """Test that the user step works."""
    # start user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # test PyViCareInvalidConfigurationError
    with patch(
        f"{MODULE}.config_flow.login",
        side_effect=PyViCareInvalidConfigurationError(
            {"error": "foo", "error_description": "bar"}
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    # test PyViCareInvalidCredentialsError
    with patch(
        f"{MODULE}.config_flow.login",
        side_effect=PyViCareInvalidCredentialsError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    # test success
    with patch(
        f"{MODULE}.config_flow.login",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ViCare"
    assert result["data"] == snapshot
    mock_setup_entry.assert_called_once()