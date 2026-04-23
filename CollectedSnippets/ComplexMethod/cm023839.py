async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    with patch(
        "pyoctoprintapi.OctoprintClient.request_app_key", return_value="test-key"
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "testuser",
                "host": "1.1.1.1",
                "name": "Printer",
                "port": 81,
                "ssl": True,
                "path": "/",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.SHOW_PROGRESS

    with (
        patch(
            "pyoctoprintapi.OctoprintClient.get_server_info",
            return_value=True,
        ),
        patch(
            "pyoctoprintapi.OctoprintClient.get_discovery_info",
            return_value=DiscoverySettings({"upnpUuid": "uuid"}),
        ),
        patch(
            "homeassistant.components.octoprint.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.octoprint.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "1.1.1.1"
    assert result2["data"] == {
        "username": "testuser",
        "host": "1.1.1.1",
        "api_key": "test-key",
        "name": "Printer",
        "port": 81,
        "ssl": True,
        "path": "/",
        "verify_ssl": True,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1