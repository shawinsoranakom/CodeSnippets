async def test_show_form(
    hass: HomeAssistant, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test show configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.srp_energy.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"], user_input=TEST_CONFIG_HOME
        )
        await hass.async_block_till_done()

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == ACCNT_NAME

        assert "data" in result
        assert result["data"][CONF_ID] == ACCNT_ID
        assert result["data"][CONF_USERNAME] == ACCNT_USERNAME
        assert result["data"][CONF_PASSWORD] == ACCNT_PASSWORD
        assert result["data"][CONF_IS_TOU] == ACCNT_IS_TOU

        captured = capsys.readouterr()
        assert "myaccount.srpnet.com" not in captured.err

        assert len(mock_setup_entry.mock_calls) == 1