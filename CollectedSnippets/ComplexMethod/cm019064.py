async def test_zero_conf_unlocked_interface_robot(hass: HomeAssistant) -> None:
    """Test zerconf which discovered already unlocked robot."""

    with patch(
        "homeassistant.components.romy.config_flow.romy.create_romy",
        return_value=_create_mocked_romy(True, True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DISCOVERY_INFO,
            context={"source": config_entries.SOURCE_ZEROCONF},
        )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4"},
    )

    assert result["data"]
    assert result["data"][CONF_HOST] == "1.2.3.4"

    assert result["result"]
    assert result["result"].unique_id == "aicu-aicgsbksisfapcjqmqjq"

    assert result["type"] is FlowResultType.CREATE_ENTRY