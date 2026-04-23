def _async_update(
        self,
        area_id: str,
        *,
        aliases: set[str] | UndefinedType = UNDEFINED,
        floor_id: str | None | UndefinedType = UNDEFINED,
        humidity_entity_id: str | None | UndefinedType = UNDEFINED,
        icon: str | None | UndefinedType = UNDEFINED,
        labels: set[str] | UndefinedType = UNDEFINED,
        name: str | UndefinedType = UNDEFINED,
        picture: str | None | UndefinedType = UNDEFINED,
        temperature_entity_id: str | None | UndefinedType = UNDEFINED,
    ) -> AreaEntry:
        """Update name of area."""
        old = self.areas[area_id]

        new_values: dict[str, Any] = {
            attr_name: value
            for attr_name, value in (
                ("aliases", aliases),
                ("floor_id", floor_id),
                ("humidity_entity_id", humidity_entity_id),
                ("icon", icon),
                ("labels", labels),
                ("picture", picture),
                ("temperature_entity_id", temperature_entity_id),
            )
            if value is not UNDEFINED and value != getattr(old, attr_name)
        }

        if "humidity_entity_id" in new_values and humidity_entity_id is not None:
            _validate_humidity_entity(self.hass, new_values["humidity_entity_id"])

        if "temperature_entity_id" in new_values and temperature_entity_id is not None:
            _validate_temperature_entity(self.hass, new_values["temperature_entity_id"])

        if name is not UNDEFINED and name != old.name:
            new_values["name"] = name

        if not new_values:
            return old

        new_values["modified_at"] = utcnow()

        self.hass.verify_event_loop_thread("area_registry.async_update")
        new = self.areas[area_id] = dataclasses.replace(old, **new_values)

        self.async_schedule_save()
        return new