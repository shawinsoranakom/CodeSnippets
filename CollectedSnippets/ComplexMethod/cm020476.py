def check_entities(entity_id_device):
        entity_id = f"sensor.{entity_id_device}_signal_level"
        state = hass.states.get(entity_id)
        assert state
        reg_ent = entity_registry.async_get(entity_id)
        assert reg_ent
        assert reg_ent.disabled is False

        entity_id = f"sensor.{entity_id_device}_ssid"
        state = hass.states.get(entity_id)
        assert state is None
        reg_ent = entity_registry.async_get(entity_id)
        assert reg_ent
        assert reg_ent.disabled is True
        assert reg_ent.disabled_by is er.RegistryEntryDisabler.INTEGRATION