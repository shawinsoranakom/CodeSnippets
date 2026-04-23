async def test_multiple_instances_with_tls_v12(hass: HomeAssistant) -> None:
    """Test we can setup a secure elk with tls v1_2."""

    elk_discovery_1 = ElkSystem("aa:bb:cc:dd:ee:ff", "127.0.0.1", 2601)
    elk_discovery_2 = ElkSystem("aa:bb:cc:dd:ee:fe", "127.0.0.2", 2601)

    with _patch_discovery(device=elk_discovery_1):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]
    assert result["step_id"] == "user"

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with _patch_elk(elk=mocked_elk):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device": elk_discovery_1.mac_address},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert not result["errors"]
    assert result2["step_id"] == "discovered_connection"
    with (
        _patch_discovery(device=elk_discovery_1),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_PROTOCOL: "TLS 1.2",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "ElkM1 ddeeff"
    assert result3["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elksv1_2://127.0.0.1",
        CONF_PASSWORD: "test-password",
        CONF_PREFIX: "",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1

    # Now try to add another instance with the different discovery info
    with _patch_discovery(device=elk_discovery_2):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]
    assert result["step_id"] == "user"

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with _patch_elk(elk=mocked_elk):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"device": elk_discovery_2.mac_address},
        )
        await hass.async_block_till_done()

    with (
        _patch_discovery(device=elk_discovery_2),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_PROTOCOL: "TLS 1.2",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "ElkM1 ddeefe"
    assert result3["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elksv1_2://127.0.0.2",
        CONF_PASSWORD: "test-password",
        CONF_PREFIX: "ddeefe",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    # Finally, try to add another instance manually with no discovery info

    with _patch_discovery(no_device=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "manual_connection"

    mocked_elk = mock_elk(invalid_auth=False, sync_complete=True)

    with (
        _patch_discovery(no_device=True),
        _patch_elk(elk=mocked_elk),
        patch(
            "homeassistant.components.elkm1.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PROTOCOL: "TLS 1.2",
                CONF_ADDRESS: "1.2.3.4",
                CONF_PREFIX: "guest_house",
                CONF_PASSWORD: "test-password",
                CONF_USERNAME: "test-username",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "guest_house"
    assert result2["data"] == {
        CONF_AUTO_CONFIGURE: True,
        CONF_HOST: "elksv1_2://1.2.3.4",
        CONF_PREFIX: "guest_house",
        CONF_PASSWORD: "test-password",
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 1