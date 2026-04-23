async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})"
    assert result2["result"].unique_id == MOCK_UUID
    assert result2["data"] == MOCK_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1