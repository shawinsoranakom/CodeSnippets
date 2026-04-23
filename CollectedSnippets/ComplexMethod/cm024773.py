async def _async_test(
        bulb_type: BulbType | None,
        model: str,
        *,
        nightlight_entity_properties: bool,
        name: str,
        entity_id: str,
        nightlight_mode_properties: bool,
    ) -> None:
        config_entry = MockConfigEntry(
            domain=DOMAIN, data={**CONFIG_ENTRY_DATA, CONF_NIGHTLIGHT_SWITCH: False}
        )
        config_entry.add_to_hass(hass)

        mocked_bulb.bulb_type = bulb_type
        model_specs = _MODEL_SPECS.get(model)
        type(mocked_bulb).get_model_specs = MagicMock(return_value=model_specs)
        original_nightlight_brightness = mocked_bulb.last_properties["nl_br"]

        mocked_bulb.last_properties["nl_br"] = "0"
        await _async_setup(config_entry)

        state = hass.states.get(entity_id)

        assert state.state == "on"
        assert state.attributes == snapshot
        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.config_entries.async_remove(config_entry.entry_id)
        entity_registry.async_clear_config_entry(config_entry.entry_id)
        mocked_bulb.last_properties["nl_br"] = original_nightlight_brightness

        # nightlight as a setting of the main entity
        if nightlight_mode_properties:
            mocked_bulb.last_properties["active_mode"] = True
            config_entry = MockConfigEntry(
                domain=DOMAIN, data={**CONFIG_ENTRY_DATA, CONF_NIGHTLIGHT_SWITCH: False}
            )
            config_entry.add_to_hass(hass)
            await _async_setup(config_entry)
            state = hass.states.get(entity_id)
            assert state.state == "on"
            assert state.attributes == snapshot(
                name=f"{request.node.callspec.id}_nightlight_mode"
            )

            await hass.config_entries.async_unload(config_entry.entry_id)
            await hass.config_entries.async_remove(config_entry.entry_id)
            entity_registry.async_clear_config_entry(config_entry.entry_id)
            await hass.async_block_till_done()
            mocked_bulb.last_properties.pop("active_mode")

        # nightlight as a separate entity
        if nightlight_entity_properties:
            config_entry = MockConfigEntry(
                domain=DOMAIN, data={**CONFIG_ENTRY_DATA, CONF_NIGHTLIGHT_SWITCH: True}
            )
            config_entry.add_to_hass(hass)
            await _async_setup(config_entry)

            assert hass.states.get(entity_id).state == "off"
            state = hass.states.get(f"{entity_id}_nightlight")
            assert state.state == "on"
            assert state.attributes == snapshot(
                name=f"{request.node.callspec.id}_nightlight_entity"
            )

            await hass.config_entries.async_unload(config_entry.entry_id)
            await hass.config_entries.async_remove(config_entry.entry_id)
            entity_registry.async_clear_config_entry(config_entry.entry_id)
            await hass.async_block_till_done()