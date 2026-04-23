async def test_form_user_flow(
    hass: HomeAssistant, mock_teltasync: MagicMock, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form and can create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "192.168.1.1",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
            CONF_VERIFY_SSL: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RUTX50 Test"
    assert result["data"] == {
        CONF_HOST: "https://192.168.1.1",
        CONF_USERNAME: "admin",
        CONF_PASSWORD: "password",
        CONF_VERIFY_SSL: False,
    }
    assert result["result"].unique_id == "1234567890"