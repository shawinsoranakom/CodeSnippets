async def _finish_user_flow(
    hass: HomeAssistant, url: str = "http://custom_url:1234"
) -> None:
    """Finish a user flow."""
    stripped_url = "http://custom_url:1234"
    result = await hass.config_entries.flow.async_init(
        otbr.DOMAIN, context={"source": "user"}
    )

    expected_data = {"url": stripped_url}

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.otbr.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": url,
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Open Thread Border Router"
    assert result["data"] == expected_data
    assert result["options"] == {}
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = result["result"]
    assert config_entry.data == expected_data
    assert config_entry.options == {}
    assert config_entry.title == "Open Thread Border Router"
    assert config_entry.unique_id == TEST_BORDER_AGENT_ID.hex()