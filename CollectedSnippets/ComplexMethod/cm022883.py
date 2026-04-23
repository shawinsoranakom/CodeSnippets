async def test_form_ssdp(hass: HomeAssistant) -> None:
    """Test we can setup from ssdp."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=f"http://{MOCK_HOSTNAME}{ISY_URL_POSTFIX}",
            upnp={
                ATTR_UPNP_FRIENDLY_NAME: "myisy",
                ATTR_UPNP_UDN: f"{UDN_UUID_PREFIX}{MOCK_UUID}",
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            PATCH_ASYNC_SETUP_ENTRY,
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"{MOCK_DEVICE_NAME} ({MOCK_HOSTNAME})"
    assert result2["result"].unique_id == MOCK_UUID
    assert result2["data"] == MOCK_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1