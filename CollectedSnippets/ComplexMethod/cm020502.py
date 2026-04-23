async def test_discovery_new_credentials_invalid(
    hass: HomeAssistant,
    mock_connect: AsyncMock,
) -> None:
    """Test setting up discovery with new invalid credentials."""
    mock_device = mock_connect["mock_devices"][IP_ADDRESS]

    with (
        patch("homeassistant.components.tplink.Discover.discover", return_value={}),
        patch(
            "homeassistant.components.tplink.config_flow.get_credentials",
            return_value=None,
        ),
        override_side_effect(mock_connect["connect"], AuthenticationError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={
                CONF_HOST: IP_ADDRESS,
                CONF_MAC: MAC_ADDRESS,
                CONF_ALIAS: ALIAS,
                CONF_DEVICE: mock_device,
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_auth_confirm"
    assert not result["errors"]

    assert mock_connect["connect"].call_count == 1

    with (
        patch(
            "homeassistant.components.tplink.config_flow.get_credentials",
            return_value=Credentials("fake_user", "fake_pass"),
        ),
        override_side_effect(mock_connect["connect"], AuthenticationError),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
        )

    assert mock_connect["connect"].call_count == 2
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "discovery_auth_confirm"

    await hass.async_block_till_done()

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {
            CONF_USERNAME: "fake_username",
            CONF_PASSWORD: "fake_password",
        },
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == CREATE_ENTRY_DATA_KLAP
    assert result3["context"]["unique_id"] == MAC_ADDRESS