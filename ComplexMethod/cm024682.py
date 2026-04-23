async def _do_assertions(expected: DeviceTestInfo) -> dr.DeviceEntry:
        # Note: homekit_controller currently uses a 3-tuple for device identifiers
        # The current standard is a 2-tuple (hkc was not migrated when this change was brought in)

        # There are currently really 3 cases here:
        # - We can match exactly one device by serial number. This won't work for devices like the Ryse.
        #   These have nlank or broken serial numbers.
        # - The device unique id is "00:00:00:00:00:00" - this is the pairing id. This is only set for
        #   the root (bridge) device.
        # - The device unique id is "00:00:00:00:00:00-X", where X is a HAP aid. This is only set when
        #   we have detected broken serial numbers (and serial number is not used as an identifier).

        device = device_registry.async_get_device(
            identifiers={(IDENTIFIER_ACCESSORY_ID, expected.unique_id)}
        )

        logger.debug("Comparing device %r to %r", device, expected)

        assert device
        assert device.name == expected.name
        assert device.model == expected.model
        assert device.manufacturer == expected.manufacturer
        assert device.hw_version == expected.hw_version
        assert device.sw_version == expected.sw_version

        # We might have matched the device by one identifier only
        # Lets check that the other one is correct. Otherwise the test might silently be wrong.
        accessory_id_set = False

        for key, value in device.identifiers:
            if key == IDENTIFIER_ACCESSORY_ID:
                assert value == expected.unique_id
                accessory_id_set = True

        # If unique_id or serial is provided it MUST actually appear in the device registry entry.
        assert (not expected.unique_id) ^ accessory_id_set

        for entity_info in expected.entities:
            entity = entity_registry.async_get(entity_info.entity_id)
            logger.debug("Comparing entity %r to %r", entity, entity_info)

            assert entity
            assert entity.device_id == device.id
            assert entity.unique_id == entity_info.unique_id
            assert entity.supported_features == entity_info.supported_features
            assert entity.entity_category == entity_info.entity_category
            assert entity.unit_of_measurement == entity_info.unit_of_measurement
            assert entity.capabilities == entity_info.capabilities

            state = hass.states.get(entity_info.entity_id)
            logger.debug("Comparing state %r to %r", state, entity_info)

            assert state is not None
            assert state.state == entity_info.state
            assert state.attributes["friendly_name"] == entity_info.friendly_name

        all_triggers = await async_get_device_automations(
            hass, DeviceAutomationType.TRIGGER, device.id
        )
        stateless_triggers = []
        for trigger in all_triggers:
            if trigger.get("entity_id"):
                continue
            stateless_triggers.append(
                DeviceTriggerInfo(
                    type=trigger.get("type"), subtype=trigger.get("subtype")
                )
            )
        assert stateless_triggers == (expected.stateless_triggers or [])

        for child in expected.devices:
            child_device = await _do_assertions(child)
            assert child_device.via_device_id == device.id
            assert child_device.id != device.id

        return device