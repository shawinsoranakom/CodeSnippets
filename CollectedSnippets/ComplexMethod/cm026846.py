def _add_entities(
        devices: set[str] | None = None, triggers: set[str] | None = None
    ) -> None:
        """Add devices and triggers."""
        if devices is None:
            devices = coordinator.new_devices
        if triggers is None:
            triggers = coordinator.new_triggers
        if not devices and not triggers:
            return
        entities = [
            FritzboxSwitch(coordinator, ain)
            for ain in devices
            if coordinator.data.devices[ain].has_switch
        ] + [FritzboxTrigger(coordinator, ain) for ain in triggers]

        async_add_entities(entities)