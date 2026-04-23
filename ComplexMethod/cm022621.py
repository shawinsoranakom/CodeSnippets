async def test_advanced_options(hass: HomeAssistant) -> None:
    """Check an options flow with advanced options."""

    config_entry = create_mock_motioneye_config_entry(hass)

    mock_client = create_mock_motioneye_client()
    with (
        patch(
            "homeassistant.components.motioneye.MotionEyeClient",
            return_value=mock_client,
        ) as mock_setup,
        patch(
            "homeassistant.components.motioneye.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        await hass.async_block_till_done()

        result = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": True}
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_WEBHOOK_SET: True,
                CONF_WEBHOOK_SET_OVERWRITE: True,
            },
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_WEBHOOK_SET]
        assert result["data"][CONF_WEBHOOK_SET_OVERWRITE]
        assert CONF_STREAM_URL_TEMPLATE not in result["data"]
        assert len(mock_setup.mock_calls) == 0
        assert len(mock_setup_entry.mock_calls) == 1

        result = await hass.config_entries.options.async_init(
            config_entry.entry_id, context={"show_advanced_options": True}
        )
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_WEBHOOK_SET: True,
                CONF_WEBHOOK_SET_OVERWRITE: True,
                CONF_STREAM_URL_TEMPLATE: "http://moo",
            },
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_WEBHOOK_SET]
        assert result["data"][CONF_WEBHOOK_SET_OVERWRITE]
        assert result["data"][CONF_STREAM_URL_TEMPLATE] == "http://moo"
        assert len(mock_setup.mock_calls) == 0
        assert len(mock_setup_entry.mock_calls) == 1