async def test_reauth(hass: HomeAssistant) -> None:
    """Test reauth flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_NAME: "DoorBird",
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    config_entry.add_to_hass(hass)
    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    flow = flows[0]

    mock_error = mock_unauthorized_exception()
    doorbirdapi = get_mock_doorbird_api(info_side_effect=mock_error)
    with patch(
        "homeassistant.components.doorbird.config_flow.DoorBird",
        return_value=doorbirdapi,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}

    doorbirdapi = get_mock_doorbird_api(info={"WIFI_MAC_ADDR": "macaddr"})
    with (
        patch(
            "homeassistant.components.doorbird.config_flow.DoorBird",
            return_value=doorbirdapi,
        ),
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            flow["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_setup.mock_calls) == 1