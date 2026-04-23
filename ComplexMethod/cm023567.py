async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "energyflip.EnergyFlip.authenticate", return_value=None
        ) as mock_authenticate,
        patch(
            "energyflip.EnergyFlip.customer_overview", return_value=None
        ) as mock_customer_overview,
        patch(
            "energyflip.EnergyFlip.get_user_id",
            return_value="test-id",
        ) as mock_get_user_id,
        patch(
            "homeassistant.components.huisbaasje.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        form_result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
            },
        )
        await hass.async_block_till_done()

    assert form_result["type"] is FlowResultType.CREATE_ENTRY
    assert form_result["title"] == "test-username"
    assert form_result["data"] == {
        "id": "test-id",
        "username": "test-username",
        "password": "test-password",
    }
    assert len(mock_authenticate.mock_calls) == 1
    assert len(mock_customer_overview.mock_calls) == 1
    assert len(mock_get_user_id.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1