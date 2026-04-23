async def test_user_flow_zwave_discovery_aborts(
    hass: HomeAssistant, mock_client: APIClient
) -> None:
    """Test that the user flow handles Z-Wave discovery abort gracefully."""
    # Mock device with Z-Wave capabilities
    mock_client.device_info = AsyncMock(
        return_value=DeviceInfo(
            uses_password=False,
            name="test-zwave-device",
            mac_address="11:22:33:44:55:DD",
            zwave_proxy_feature_flags=1,
            zwave_home_id=9876543210,
        )
    )
    mock_client.connected_address = "192.168.1.102"

    # Track flow.async_init calls
    original_async_init = hass.config_entries.flow.async_init
    flow_init_calls = []

    async def track_async_init(*args, **kwargs):
        flow_init_calls.append((args, kwargs))
        # For the Z-Wave flow, return an ABORT result
        if args and args[0] == "zwave_js":
            return {
                "type": FlowResultType.ABORT,
                "reason": "already_configured",
            }
        # Otherwise call the original
        return await original_async_init(*args, **kwargs)

    with patch.object(
        hass.config_entries.flow, "async_init", side_effect=track_async_init
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_HOST: "192.168.1.102", CONF_PORT: 6053},
        )

    # Verify the ESPHome entry was still created despite Z-Wave flow aborting
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-zwave-device"
    assert result["data"] == {
        CONF_HOST: "192.168.1.102",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
        CONF_DEVICE_NAME: "test-zwave-device",
    }

    # Verify Z-Wave discovery flow was attempted
    assert len(flow_init_calls) == 2
    zwave_call_args, zwave_call_kwargs = flow_init_calls[1]
    assert zwave_call_args[0] == "zwave_js"
    assert zwave_call_kwargs["context"]["source"] == config_entries.SOURCE_ESPHOME
    assert zwave_call_kwargs["context"]["discovery_key"] == discovery_flow.DiscoveryKey(
        domain=DOMAIN,
        key="11:22:33:44:55:DD",
        version=1,
    )
    assert zwave_call_kwargs["data"] == ESPHomeServiceInfo(
        name="test-zwave-device",
        zwave_home_id=9876543210,
        ip_address="192.168.1.102",
        port=6053,
        noise_psk=None,
    )

    # Verify next_flow was NOT set since Z-Wave flow aborted
    assert "next_flow" not in result