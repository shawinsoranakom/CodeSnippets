async def async_call_service(
        self, domain: str, service: str, intent_obj: Intent, state: State
    ) -> None:
        """Call service on entity."""
        hass = intent_obj.hass

        service_data: dict[str, Any] = {ATTR_ENTITY_ID: state.entity_id}
        if self.required_slots:
            for key, slot_info in self.required_slots.items():
                service_data[slot_info.service_data_name or key] = intent_obj.slots[
                    key
                ]["value"]

        if self.optional_slots:
            for key, slot_info in self.optional_slots.items():
                if value := intent_obj.slots.get(key):
                    service_data[slot_info.service_data_name or key] = value["value"]

        await self._run_then_background(
            hass.async_create_task_internal(
                hass.services.async_call(
                    domain,
                    service,
                    service_data,
                    context=intent_obj.context,
                    blocking=True,
                ),
                f"intent_call_service_{domain}_{service}",
            )
        )