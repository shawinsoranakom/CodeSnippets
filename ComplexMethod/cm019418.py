async def test_entry_and_subentry(
    hass: HomeAssistant, get_data: MockRestData, mock_setup_entry: AsyncMock
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["step_id"] == "user"
    assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.rest.RestData",
        return_value=get_data,
    ) as mock_data:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_RESOURCE: "https://www.home-assistant.io",
                CONF_METHOD: "GET",
                CONF_AUTH: {},
                CONF_ADVANCED: {
                    CONF_VERIFY_SSL: True,
                    CONF_TIMEOUT: 10.0,
                },
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["version"] == 2
    assert result["options"] == {
        CONF_RESOURCE: "https://www.home-assistant.io",
        CONF_METHOD: "GET",
        CONF_AUTH: {},
        CONF_ADVANCED: {
            CONF_VERIFY_SSL: True,
            CONF_TIMEOUT: 10.0,
            CONF_ENCODING: "UTF-8",
        },
    }

    assert len(mock_data.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    await hass.async_block_till_done(wait_background_tasks=True)

    subentry_flows = hass.config_entries.subentries.async_progress()
    assert len(subentry_flows) == 1

    result = await hass.config_entries.subentries.async_configure(
        subentry_flows[0]["flow_id"],
        {
            CONF_NAME: "Current version",
            CONF_INDEX: 0,
            CONF_SELECT: ".current-version h1",
            CONF_ADVANCED: {},
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Current version"
    assert result["data"] == {
        CONF_INDEX: 0,
        CONF_SELECT: ".current-version h1",
        CONF_ADVANCED: {},
    }