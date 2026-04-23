async def test_full_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_flipr_client: AsyncMock
) -> None:
    """Test the full flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_EMAIL: "dummylogin",
            CONF_PASSWORD: "dummypass",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Flipr dummylogin"
    assert result["result"].unique_id == "dummylogin"
    assert result["data"] == {
        CONF_EMAIL: "dummylogin",
        CONF_PASSWORD: "dummypass",
    }