async def test_user_flow(hass: HomeAssistant) -> None:
    """Test the user flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.osoenergy.config_flow.OSOEnergy.get_user_email",
            return_value=TEST_USER_EMAIL,
        ),
        patch(
            "homeassistant.components.osoenergy.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_API_KEY: SUBSCRIPTION_KEY},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == TEST_USER_EMAIL
    assert result2["data"] == {
        CONF_API_KEY: SUBSCRIPTION_KEY,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1