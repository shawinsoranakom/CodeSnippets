async def test_data_secure_group_key_issue_repair_flow(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    knx: KNXTestKit,
) -> None:
    """Test repair flow for DataSecure group key issue."""
    await knx.setup_integration(
        {
            "switch": [
                {"name": "Test 1", "address": "1/2/5"},
                {"name": "Test 2", "address": "11/0/0"},
            ]
        }
    )

    knx.receive_data_secure_issue("11/0/0", source="1.0.1")
    knx.receive_data_secure_issue("1/2/5", source="1.0.10")
    knx.receive_data_secure_issue("1/2/5", source="1.0.1")
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue(DOMAIN, REPAIR_ISSUE_DATA_SECURE_GROUP_KEY)
    assert issue is not None
    assert issue.translation_placeholders == {
        "addresses": "`1/2/5` from 1.0.1, 1.0.10\n`11/0/0` from 1.0.1",  # check sorting
        "interface": "0.0.0",
    }

    issues = await get_repairs(hass, hass_ws_client)
    assert issues

    await async_process_repairs_platforms(hass)
    client = await hass_client()
    flow = await start_repair_fix_flow(
        client, DOMAIN, REPAIR_ISSUE_DATA_SECURE_GROUP_KEY
    )

    flow_id = flow["flow_id"]
    assert flow["type"] == FlowResultType.FORM
    assert flow["step_id"] == "secure_knxkeys"

    # test error handling
    with patch_file_upload(
        side_effect=InvalidSecureConfiguration(),
    ):
        flow = await process_repair_fix_flow(
            client,
            flow_id,
            {
                repairs.CONF_KEYRING_FILE: FIXTURE_UPLOAD_UUID,
                CONF_KNX_KNXKEY_PASSWORD: "invalid_password_mocked",
            },
        )
    assert flow["type"] == FlowResultType.FORM
    assert flow["step_id"] == "secure_knxkeys"
    assert flow["errors"] == {CONF_KNX_KNXKEY_PASSWORD: "keyfile_invalid_signature"}

    # test successful file upload
    with patch_file_upload():
        flow = await process_repair_fix_flow(
            client,
            flow_id,
            {
                repairs.CONF_KEYRING_FILE: FIXTURE_UPLOAD_UUID,
                CONF_KNX_KNXKEY_PASSWORD: "password",
            },
        )
    assert flow["type"] == FlowResultType.CREATE_ENTRY
    assert (
        issue_registry.async_get_issue(DOMAIN, REPAIR_ISSUE_DATA_SECURE_GROUP_KEY)
        is None
    )