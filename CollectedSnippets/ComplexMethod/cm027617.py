def slot_schema(self) -> dict:
        """Return a slot schema."""
        domain_validator = (
            vol.In(list(self.required_domains)) if self.required_domains else cv.string
        )
        slot_schema = {
            vol.Any("name", "area", "floor"): non_empty_string,
            vol.Optional("domain"): vol.All(cv.ensure_list, [domain_validator]),
        }
        if self.device_classes:
            # The typical way to match enums is with vol.Coerce, but we build a
            # flat list to make the API simpler to describe programmatically
            flattened_device_classes = vol.In(
                [
                    device_class.value
                    for device_class_enum in self.device_classes
                    for device_class in device_class_enum
                ]
            )
            slot_schema.update(
                {
                    vol.Optional("device_class"): vol.All(
                        cv.ensure_list,
                        [flattened_device_classes],
                    )
                }
            )

        slot_schema.update(
            {
                vol.Optional("preferred_area_id"): cv.string,
                vol.Optional("preferred_floor_id"): cv.string,
            }
        )

        if self.required_slots:
            slot_schema.update(
                {
                    vol.Required(
                        key, description=slot_info.description
                    ): slot_info.value_schema
                    for key, slot_info in self.required_slots.items()
                }
            )

        if self.optional_slots:
            slot_schema.update(
                {
                    vol.Optional(
                        key, description=slot_info.description
                    ): slot_info.value_schema
                    for key, slot_info in self.optional_slots.items()
                }
            )

        return slot_schema