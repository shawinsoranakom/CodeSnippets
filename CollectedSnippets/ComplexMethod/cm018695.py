async def test_hassio_discovery_flow_2x_addons(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, otbr_addon_info
) -> None:
    """Test the hassio discovery flow when the user has 2 addons with otbr support."""
    url1 = "http://core-silabs-multiprotocol:8081"
    url2 = "http://core-silabs-multiprotocol_2:8081"
    aioclient_mock.get(f"{url1}/node/dataset/active", text="aa")
    aioclient_mock.get(f"{url2}/node/dataset/active", text="bb")
    aioclient_mock.get(f"{url1}/node/ba-id", json=TEST_BORDER_AGENT_ID.hex())
    aioclient_mock.get(f"{url2}/node/ba-id", json=TEST_BORDER_AGENT_ID_2.hex())

    async def _addon_info(slug: str) -> Mock:
        await asyncio.sleep(0)
        if slug == "otbr":
            device = (
                "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_"
                "9e2adbd75b8beb119fe564a0f320645d-if00-port0"
            )
        else:
            device = (
                "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_"
                "9e2adbd75b8beb119fe564a0f320645d-if00-port1"
            )
        return Mock(
            available=True,
            hostname=otbr_addon_info.return_value.hostname,
            options={"device": device},
            state=otbr_addon_info.return_value.state,
            update_available=otbr_addon_info.return_value.update_available,
            version=otbr_addon_info.return_value.version,
        )

    otbr_addon_info.side_effect = _addon_info

    result1 = await hass.config_entries.flow.async_init(
        otbr.DOMAIN, context={"source": "hassio"}, data=HASSIO_DATA
    )
    result2 = await hass.config_entries.flow.async_init(
        otbr.DOMAIN, context={"source": "hassio"}, data=HASSIO_DATA_2
    )

    results = [result1, result2]

    expected_data = {
        "url": f"http://{HASSIO_DATA.config['host']}:{HASSIO_DATA.config['port']}",
    }
    expected_data_2 = {
        "url": f"http://{HASSIO_DATA_2.config['host']}:{HASSIO_DATA_2.config['port']}",
    }

    assert results[0]["type"] is FlowResultType.CREATE_ENTRY
    assert (
        results[0]["title"]
        == "Home Assistant Connect ZBT-1 (Silicon Labs Multiprotocol)"
    )
    assert results[0]["data"] == expected_data
    assert results[0]["options"] == {}

    assert results[1]["type"] is FlowResultType.CREATE_ENTRY
    assert (
        results[1]["title"]
        == "Home Assistant Connect ZBT-1 (Silicon Labs Multiprotocol)"
    )
    assert results[1]["data"] == expected_data_2
    assert results[1]["options"] == {}

    assert len(hass.config_entries.async_entries(otbr.DOMAIN)) == 2

    config_entry = hass.config_entries.async_entries(otbr.DOMAIN)[0]
    assert config_entry.data == expected_data
    assert config_entry.options == {}
    assert (
        config_entry.title
        == "Home Assistant Connect ZBT-1 (Silicon Labs Multiprotocol)"
    )
    assert config_entry.unique_id == HASSIO_DATA.uuid

    config_entry = hass.config_entries.async_entries(otbr.DOMAIN)[1]
    assert config_entry.data == expected_data_2
    assert config_entry.options == {}
    assert (
        config_entry.title
        == "Home Assistant Connect ZBT-1 (Silicon Labs Multiprotocol)"
    )
    assert config_entry.unique_id == HASSIO_DATA_2.uuid