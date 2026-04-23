async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            side_effect=NUTError("no route to host"),
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=NUTError("no route to host"),
        ),
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

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
    assert result2["description_placeholders"] == {"error": "no route to host"}

    with (
        patch(
            "homeassistant.components.nut.AIONUTClient.list_ups",
            return_value={"ups1"},
        ),
        patch(
            "homeassistant.components.nut.AIONUTClient.list_vars",
            side_effect=Exception,
        ),
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

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}

    mock_pynut = _get_mock_nutclient(
        list_vars={"battery.voltage": "voltage", "ups.status": "OL"}, list_ups=["ups1"]
    )
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
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.1.1.1",
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_PORT: 2222,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "1.1.1.1:2222"
    assert result2["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_PORT: 2222,
        CONF_USERNAME: "test-username",
    }
    assert len(mock_setup_entry.mock_calls) == 1