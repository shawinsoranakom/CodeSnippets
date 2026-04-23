async def test_form(hass: HomeAssistant, mock_list_contracts) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.prosegur.config_flow.Installation.list",
            return_value=mock_list_contracts,
        ) as mock_retrieve,
        patch(
            "homeassistant.components.prosegur.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password",
                "country": "PT",
            },
        )
        await hass.async_block_till_done()

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"contract": "123"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Contract 123"
    assert result3["data"] == {
        "contract": "123",
        "username": "test-username",
        "password": "test-password",
        "country": "PT",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    assert len(mock_retrieve.mock_calls) == 1