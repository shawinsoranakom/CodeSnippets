async def test_user_is_setting_up_lock_and_discovery_happens_in_the_middle(
    hass: HomeAssistant,
) -> None:
    """Test that the user is setting up the lock and waiting for validation and the keys get discovered.

    In this case the integration discovery should abort and let the user continue setting up the lock.
    """
    with patch(
        "homeassistant.components.yalexs_ble.config_flow.async_discovered_service_info",
        return_value=[NOT_YALE_DISCOVERY_INFO, YALE_ACCESS_LOCK_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "key_slot"

    user_flow_event = asyncio.Event()
    valdidate_started = asyncio.Event()

    async def _wait_for_user_flow():
        valdidate_started.set()
        await user_flow_event.wait()

    with (
        patch(
            "homeassistant.components.yalexs_ble.config_flow.PushLock.validate",
            side_effect=_wait_for_user_flow,
        ),
        patch(
            "homeassistant.components.yalexs_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        user_flow_task = asyncio.create_task(
            hass.config_entries.flow.async_configure(
                result2["flow_id"],
                {
                    CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
                    CONF_SLOT: 66,
                },
            )
        )
        await valdidate_started.wait()

        with patch(
            "homeassistant.components.yalexs_ble.util.async_discovered_service_info",
            return_value=[LOCK_DISCOVERY_INFO_UUID_ADDRESS],
        ):
            discovery_result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
                data={
                    "name": "Front Door",
                    "address": OLD_FIRMWARE_LOCK_DISCOVERY_INFO.address,
                    "key": "2fd51b8621c6a139eaffbedcb846b60f",
                    "slot": 66,
                    "serial": "M1XXX012LU",
                },
            )
            await hass.async_block_till_done()
        assert discovery_result["type"] is FlowResultType.ABORT
        assert discovery_result["reason"] == "already_in_progress"

        user_flow_event.set()
        user_flow_result = await user_flow_task

    assert user_flow_result["type"] is FlowResultType.CREATE_ENTRY
    assert user_flow_result["title"] == f"{YALE_ACCESS_LOCK_DISCOVERY_INFO.name} (EEFF)"
    assert user_flow_result["data"] == {
        CONF_LOCAL_NAME: YALE_ACCESS_LOCK_DISCOVERY_INFO.name,
        CONF_ADDRESS: YALE_ACCESS_LOCK_DISCOVERY_INFO.address,
        CONF_KEY: "2fd51b8621c6a139eaffbedcb846b60f",
        CONF_SLOT: 66,
    }
    assert (
        user_flow_result["result"].unique_id == YALE_ACCESS_LOCK_DISCOVERY_INFO.address
    )
    assert len(mock_setup_entry.mock_calls) == 1