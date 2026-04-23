async def test_reauth(hass: HomeAssistant) -> None:
    """Test reauthentication."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DKEY_DISCOVERY_INFO.address,
        data={"address": DKEY_DISCOVERY_INFO.address},
    )
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_last_service_info",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "no_longer_in_range"}

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_last_service_info",
        return_value=DKEY_DISCOVERY_INFO,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "associate"
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.dormakaba_dkey.config_flow.DKEYLock.associate",
            return_value=AssociationData(b"1234", b"AABBCCDD"),
        ) as mock_associate,
        patch(
            "homeassistant.components.dormakaba_dkey.async_setup_entry",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"activation_code": "1234-1234"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {
        CONF_ADDRESS: DKEY_DISCOVERY_INFO.address,
        "association_data": {"key_holder_id": "31323334", "secret": "4141424243434444"},
    }
    mock_associate.assert_awaited_once_with("1234-1234")