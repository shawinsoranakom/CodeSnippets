async def test_autodetect_auth_missing(hass: HomeAssistant) -> None:
    """Test for send key with autodetection of protocol."""
    with patch(
        "homeassistant.components.samsungtv.bridge.Remote",
        side_effect=AccessDenied("Boom"),
    ) as remote:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}, data=MOCK_USER_DATA
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "pairing"
        assert result["errors"] == {"base": "auth_missing"}

        assert remote.call_count == 2
        assert remote.call_args_list == [
            call(AUTODETECT_LEGACY),
            call(AUTODETECT_LEGACY),
        ]
    with patch("homeassistant.components.samsungtv.bridge.Remote", side_effect=OSError):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()
        assert result2["type"] is FlowResultType.ABORT
        assert result2["reason"] == RESULT_CANNOT_CONNECT