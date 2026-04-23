async def test_form_user_multiple_aliases(hass: HomeAssistant) -> None:
    """Test we can configure device with multiple aliases."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "2.2.2.2", CONF_PORT: 123, CONF_RESOURCES: ["battery.charge"]},
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage"},
        list_ups={"ups1": "UPS 1", "ups2": "UPS2"},
    )

    with patch(
        "homeassistant.components.nut.AIONUTClient",
        return_value=mock_pynut,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )

    assert result2["step_id"] == "ups"
    assert result2["type"] is FlowResultType.FORM

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient",
            return_value=mock_pynut,
        ),
        patch(
            "homeassistant.components.nut.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ALIAS: "ups2"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "ups2@1.1.1.1:2222"
    assert result3["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_ALIAS: "ups2",
        CONF_PORT: 2222,
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 2