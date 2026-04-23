async def test_user_flow_succeeds_during_zeroconf_discovery(
    hass: HomeAssistant, mock_airq: AsyncMock
) -> None:
    """Test manual user flow does not abort when a zeroconf flow is in progress.

    Regression test: before raise_on_progress=False, initiating a manual
    setup while zeroconf discovery was pending for the same device would
    abort with ``already_in_progress``.
    """
    # 1. Start a zeroconf discovery flow — this sets unique_id and waits
    #    for the user to confirm (enter password).
    zeroconf_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=IPv4Address("192.168.0.123"),
            ip_addresses=[IPv4Address("192.168.0.123")],
            port=80,
            hostname="airq.local.",
            type="_http._tcp.local.",
            name="air-Q._http._tcp.local.",
            # Use the same ID as TEST_DEVICE_INFO so both flows share
            # the unique_id.
            properties={
                "device": "air-q",
                "devicename": "My air-Q",
                "id": TEST_DEVICE_INFO["id"],
            },
        ),
    )
    assert zeroconf_result["type"] is FlowResultType.FORM
    assert zeroconf_result["step_id"] == "discovery_confirm"

    # 2. While the zeroconf flow is pending, start a manual user flow.
    user_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert user_result["type"] is FlowResultType.FORM

    # 3. Complete the manual flow — this should NOT abort with
    #    "already_in_progress".
    user_result2 = await hass.config_entries.flow.async_configure(
        user_result["flow_id"], TEST_USER_DATA
    )
    await hass.async_block_till_done()

    assert user_result2["type"] is FlowResultType.CREATE_ENTRY
    assert user_result2["title"] == TEST_DEVICE_INFO["name"]
    assert user_result2["data"] == TEST_USER_DATA

    # 4. The zeroconf discovery flow should now be aborted: completing
    #    the user flow created a config entry for this unique_id, so
    #    the pending discovery flow is no longer valid.
    ongoing_flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert not ongoing_flows, f"Expected no remaining flows, but found: {ongoing_flows}"