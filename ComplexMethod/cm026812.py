async def async_configure_accessories(self) -> list[State]:
        """Configure accessories for the included states."""
        dev_reg = dr.async_get(self.hass)
        ent_reg = er.async_get(self.hass)
        device_lookup: dict[str, dict[tuple[str, str | None], str]] = {}
        entity_states: list[State] = []
        entity_filter = self._filter.get_filter()
        entries = ent_reg.entities
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            if not entity_filter(entity_id):
                continue

            if ent_reg_ent := ent_reg.async_get(entity_id):
                if (
                    ent_reg_ent.entity_category is not None
                    or ent_reg_ent.hidden_by is not None
                ) and not self._filter.explicitly_included(entity_id):
                    continue

                await self._async_set_device_info_attributes(
                    ent_reg_ent, dev_reg, entity_id
                )
                if device_id := ent_reg_ent.device_id:
                    if device_id not in device_lookup:
                        device_lookup[device_id] = {
                            (
                                entry.domain,
                                entry.device_class or entry.original_device_class,
                            ): entry.entity_id
                            for entry in entries.get_entries_for_device_id(device_id)
                        }
                    self._async_configure_linked_sensors(
                        ent_reg_ent, device_lookup[device_id], state
                    )

            entity_states.append(state)

        return entity_states