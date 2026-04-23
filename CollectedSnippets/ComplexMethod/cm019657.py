async def test_options_with_targets(hass: HomeAssistant, reversed) -> None:
    """Test we can configure reverse for a target."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "1.1.1.1", CONF_PORT: 12, CONF_SYSTEM_ID: "46"},
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.somfy_mylink.SomfyMyLinkSynergy.status_info",
        return_value={
            "result": [
                {
                    "targetID": "a",
                    "name": "Master Window",
                    "type": 0,
                }
            ]
        },
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(config_entry.entry_id)
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"target_id": "a"},
        )

        assert result2["type"] is FlowResultType.FORM
        result3 = await hass.config_entries.options.async_configure(
            result2["flow_id"],
            user_input={"reverse": reversed},
        )

        assert result3["type"] is FlowResultType.FORM

        result4 = await hass.config_entries.options.async_configure(
            result3["flow_id"],
            user_input={"target_id": None},
        )
        assert result4["type"] is FlowResultType.CREATE_ENTRY

        assert config_entry.options == {
            CONF_REVERSED_TARGET_IDS: {"a": reversed},
        }

        await hass.async_block_till_done()