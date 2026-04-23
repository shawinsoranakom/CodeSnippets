async def test_mdns_update_to_paired_during_pairing(
    hass: HomeAssistant, controller
) -> None:
    """Test we do not abort pairing if mdns is updated to reflect paired during pairing."""
    device = setup_mock_accessory(controller)
    discovery_info = get_device_discovery_info(device)
    discovery_info_paired = get_device_discovery_info(device, paired=True)

    # Device is discovered
    result = await hass.config_entries.flow.async_init(
        "homekit_controller",
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert get_flow_context(hass, result) == {
        "title_placeholders": {"name": "TestDevice", "category": "Outlet"},
        "unique_id": "00:00:00:00:00:00",
        "source": config_entries.SOURCE_ZEROCONF,
    }

    finish_pairing_started = asyncio.Event()
    mdns_update_to_paired = asyncio.Event()

    original_async_start_pairing = device.async_start_pairing

    async def _async_start_pairing(*args, **kwargs):
        finish_pairing = await original_async_start_pairing(*args, **kwargs)

        async def _finish_pairing(*args, **kwargs):
            finish_pairing_started.set()
            # Insert an event wait to make sure
            # we trigger the mdns update in the middle of the pairing
            await mdns_update_to_paired.wait()
            return await finish_pairing(*args, **kwargs)

        return _finish_pairing

    with patch.object(device, "async_start_pairing", _async_start_pairing):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert get_flow_context(hass, result) == {
        "dismiss_protected": True,
        "title_placeholders": {"name": "TestDevice", "category": "Outlet"},
        "unique_id": "00:00:00:00:00:00",
        "source": config_entries.SOURCE_ZEROCONF,
    }

    # User enters pairing code
    task = asyncio.create_task(
        hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"pairing_code": "111-22-333"}
        )
    )
    # Ensure the task starts
    await finish_pairing_started.wait()
    # Make sure when the device is discovered as paired via mdns
    # it does not abort pairing if it happens before pairing is finished
    result2 = await hass.config_entries.flow.async_init(
        "homekit_controller",
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info_paired,
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_paired"
    mdns_update_to_paired.set()
    result = await task
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Koogeek-LS1-20833F"
    assert result["data"] == {}