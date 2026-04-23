async def test_form(hass: HomeAssistant, picnic_api) -> None:
    """Test we get the form and a config entry is created."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.picnic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country_code": "NL",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Picnic"
    assert result2["data"] == {
        CONF_ACCESS_TOKEN: picnic_api().session.auth_token,
        CONF_COUNTRY_CODE: "NL",
    }
    assert len(mock_setup_entry.mock_calls) == 1