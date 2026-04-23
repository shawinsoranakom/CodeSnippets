async def test_user_api_1(
    hass: HomeAssistant,
    mock_slide_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_slide_api.slide_info.side_effect = [
        None,
        get_data(),
    ]

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: HOST,
            CONF_PASSWORD: "pwd",
        },
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == HOST
    assert result2["data"][CONF_HOST] == HOST
    assert result2["data"][CONF_PASSWORD] == "pwd"
    assert result2["data"][CONF_API_VERSION] == 1
    assert result2["result"].unique_id == "12:34:56:78:90:ab"
    assert not result2["options"][CONF_INVERT_POSITION]
    assert len(mock_setup_entry.mock_calls) == 1