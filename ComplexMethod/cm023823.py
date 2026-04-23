async def test_zeroconf_already_configured_refresh_token(hass: HomeAssistant) -> None:
    """Test starting a flow from zeroconf when already configured and the token is out of date."""
    entry2 = MockConfigEntry(
        domain=DOMAIN,
        unique_id="not-the-same-bond-id",
        data={CONF_HOST: "stored-host", CONF_ACCESS_TOKEN: "correct-token"},
    )
    entry2.add_to_hass(hass)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="already-registered-bond-id",
        data={CONF_HOST: "stored-host", CONF_ACCESS_TOKEN: "incorrect-token"},
    )
    entry.add_to_hass(hass)

    with patch_bond_version(
        side_effect=ClientResponseError(MagicMock(), MagicMock(), status=401)
    ):
        await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR

    with (
        _patch_async_setup_entry() as mock_setup_entry,
        patch_bond_token(return_value={"token": "discovered-token"}),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("127.0.0.2"),
                ip_addresses=[ip_address("127.0.0.2")],
                hostname="mock_hostname",
                name="already-registered-bond-id.some-other-tail-info",
                port=None,
                properties={},
                type="mock_type",
            ),
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data["host"] == "127.0.0.2"
    assert entry.data[CONF_ACCESS_TOKEN] == "discovered-token"
    # entry2 should not get changed
    assert entry2.data[CONF_ACCESS_TOKEN] == "correct-token"
    assert len(mock_setup_entry.mock_calls) == 1