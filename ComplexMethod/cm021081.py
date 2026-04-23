async def test_user_flow_starts_zwave_discovery(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test that the user flow starts Z-Wave JS discovery when device has Z-Wave capabilities."""
    # Mock device with Z-Wave capabilities
    mock_client.device_info = AsyncMock(
        return_value=DeviceInfo(
            uses_password=False,
            name="test-zwave-device",
            mac_address="11:22:33:44:55:BB",
            zwave_proxy_feature_flags=1,
            zwave_home_id=1234567890,
        )
    )
    mock_client.connected_address = "mock-connected-address"

    # Track flow.async_init calls and async_get calls
    original_async_init = hass.config_entries.flow.async_init
    original_async_get = hass.config_entries.flow.async_get
    flow_init_calls = []
    zwave_flow_id = "mock-zwave-flow-id"

    async def track_async_init(*args, **kwargs):
        flow_init_calls.append((args, kwargs))
        # For the Z-Wave flow, return a mock result with the flow_id
        if args and args[0] == "zwave_js":
            return {"flow_id": zwave_flow_id, "type": FlowResultType.FORM}
        # Otherwise call the original
        return await original_async_init(*args, **kwargs)

    def mock_async_get(flow_id: str):
        # Return a mock flow for the Z-Wave flow_id
        if flow_id == zwave_flow_id:
            return MagicMock()
        return original_async_get(flow_id)

    with (
        patch.object(
            hass.config_entries.flow, "async_init", side_effect=track_async_init
        ),
        patch.object(hass.config_entries.flow, "async_get", side_effect=mock_async_get),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.168.1.100", CONF_PORT: 6053},
        )

    # Verify the entry was created
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-zwave-device"
    assert result["data"] == {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
        CONF_DEVICE_NAME: "test-zwave-device",
    }

    # First call is ESPHome flow, second should be Z-Wave flow
    assert len(flow_init_calls) == 2
    zwave_call_args, zwave_call_kwargs = flow_init_calls[1]
    assert zwave_call_args[0] == "zwave_js"
    assert zwave_call_kwargs["context"] == {
        "source": config_entries.SOURCE_ESPHOME,
        "discovery_key": discovery_flow.DiscoveryKey(
            domain="esphome", key="11:22:33:44:55:BB", version=1
        ),
    }
    assert zwave_call_kwargs["data"] == ESPHomeServiceInfo(
        name="test-zwave-device",
        zwave_home_id=1234567890,
        ip_address="mock-connected-address",
        port=6053,
        noise_psk=None,
    )

    # Verify next_flow was set
    assert result["next_flow"] == (config_entries.FlowType.CONFIG_FLOW, zwave_flow_id)