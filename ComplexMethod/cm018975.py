async def test_zeroconf_flow_auth(
    hass: HomeAssistant,
    mock_smlight_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full zeroconf flow including authentication."""
    mock_smlight_client.check_auth_needed.return_value = True

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    assert result["description_placeholders"] == {"host": MOCK_DEVICE_NAME}
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_discovery"

    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0]["flow_id"] == result["flow_id"]
    assert progress[0]["context"]["confirm_only"] is True

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "auth"

    progress2 = hass.config_entries.flow.async_progress()
    assert len(progress2) == 1
    assert progress2[0]["flow_id"] == result["flow_id"]

    result3 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: MOCK_USERNAME,
            CONF_PASSWORD: MOCK_PASSWORD,
        },
    )

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["context"]["source"] == "zeroconf"
    assert result3["context"]["unique_id"] == "aa:bb:cc:dd:ee:ff"
    assert result3["title"] == "SLZB-06p7"
    assert result3["data"] == {
        CONF_USERNAME: MOCK_USERNAME,
        CONF_PASSWORD: MOCK_PASSWORD,
        CONF_HOST: MOCK_HOST,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_smlight_client.get_info.mock_calls) == 2