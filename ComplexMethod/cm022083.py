async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONNECTION_TYPE: CLOUD,
        },
    )
    assert result2["type"] is FlowResultType.FORM

    with (
        patch(
            "adax.get_adax_token",
            return_value="test_token",
        ),
        patch(
            "homeassistant.components.adax.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            TEST_DATA,
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == str(TEST_DATA["account_id"])
    assert result3["data"] == {
        ACCOUNT_ID: TEST_DATA["account_id"],
        CONF_PASSWORD: TEST_DATA["password"],
        CONNECTION_TYPE: CLOUD,
    }
    assert len(mock_setup_entry.mock_calls) == 1