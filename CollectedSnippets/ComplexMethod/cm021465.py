async def test_hassio_success(
    hass: HomeAssistant,
    mock_mealie_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test successful Supervisor flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={"addon": "Mealie", "host": "http://test", "port": 9090},
            name="mealie",
            slug="mealie",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "hassio_confirm"
    assert result.get("description_placeholders") == {"addon": "Mealie"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_TOKEN: "token"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Mealie"
    assert result["data"] == {
        CONF_HOST: "http://test:9090",
        CONF_API_TOKEN: "token",
        CONF_VERIFY_SSL: True,
    }
    assert result["result"].unique_id == "bf1c62fe-4941-4332-9886-e54e88dbdba0"