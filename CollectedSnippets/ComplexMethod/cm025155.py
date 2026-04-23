def add_suggested_values_to_schema(
        self, data_schema: vol.Schema, suggested_values: Mapping[str, Any] | None
    ) -> vol.Schema:
        """Make a copy of the schema, populated with suggested values.

        For each schema marker matching items in `suggested_values`,
        the `suggested_value` will be set. The existing `suggested_value` will
        be left untouched if there is no matching item.
        """
        schema = {}
        for key, val in data_schema.schema.items():
            if isinstance(key, vol.Marker):
                # Exclude advanced field
                if (
                    key.description
                    and key.description.get("advanced")
                    and not self.show_advanced_options
                ):
                    continue

            # Process the section schema options
            if (
                suggested_values is not None
                and isinstance(val, section)
                and key in suggested_values
            ):
                new_section_key = copy.copy(key)
                new_val = copy.copy(val)
                schema[new_section_key] = new_val
                new_val.schema = self.add_suggested_values_to_schema(
                    new_val.schema, suggested_values[key]
                )
                continue

            new_key = key
            if (
                suggested_values
                and key in suggested_values
                and isinstance(key, vol.Marker)
            ):
                # Copy the marker to not modify the flow schema
                new_key = copy.copy(key)
                new_key.description = {"suggested_value": suggested_values[key.schema]}
            schema[new_key] = val
        return vol.Schema(schema)