async def test_import_yaml_config(
    hass: HomeAssistant, mock_client: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test importing YAML configuration."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={
            CONF_HOST: "192.168.1.72",
            CONF_PORT: 4999,
            CONF_INFER_ARMING_STATE: False,
            CONF_ZONES: [
                {CONF_ZONE_NAME: "Garage", CONF_ZONE_ID: 1},
                {
                    CONF_ZONE_NAME: "Front Door",
                    CONF_ZONE_ID: 5,
                    CONF_ZONE_TYPE: BinarySensorDeviceClass.DOOR,
                },
            ],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Ness Alarm 192.168.1.72:4999"
    assert result["data"] == {
        CONF_HOST: "192.168.1.72",
        CONF_PORT: 4999,
        CONF_INFER_ARMING_STATE: False,
    }

    # Check that subentries were created for zones with names preserved
    assert len(result["subentries"]) == 2
    assert result["subentries"][0]["title"] == "Zone 1"
    assert result["subentries"][0]["unique_id"] == "zone_1"
    assert result["subentries"][0]["data"][CONF_TYPE] == BinarySensorDeviceClass.MOTION
    assert result["subentries"][0]["data"][CONF_ZONE_NAME] == "Garage"
    assert result["subentries"][1]["title"] == "Zone 5"
    assert result["subentries"][1]["unique_id"] == "zone_5"
    assert result["subentries"][1]["data"][CONF_TYPE] == BinarySensorDeviceClass.DOOR
    assert result["subentries"][1]["data"][CONF_ZONE_NAME] == "Front Door"

    assert len(mock_setup_entry.mock_calls) == 1
    mock_client.close.assert_awaited_once()