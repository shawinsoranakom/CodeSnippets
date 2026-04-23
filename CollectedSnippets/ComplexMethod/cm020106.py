async def test_tunneling_setup_manual(
    gateway_scanner_mock: MagicMock,
    hass: HomeAssistant,
    knx_setup,
    user_input,
    title,
    config_entry_data,
) -> None:
    """Test tunneling if no gateway was found found (or `manual` option was chosen)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_tunnel"
    assert result["errors"] == {"base": "no_tunnel_discovered"}

    with patch(
        "homeassistant.components.knx.config_flow.request_description",
        return_value=_gateway_descriptor(
            user_input[CONF_HOST],
            user_input[CONF_PORT],
            supports_tunnelling_tcp=(
                user_input[CONF_KNX_TUNNELING_TYPE] == CONF_KNX_TUNNELING_TCP
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input,
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == title
    assert result["data"] == config_entry_data
    knx_setup.assert_called_once()