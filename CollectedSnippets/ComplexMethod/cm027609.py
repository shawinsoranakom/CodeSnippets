def _update_and_remove_omitted_optional_keys(
        self,
        values: dict[str, Any],
        user_input: dict[str, Any],
        data_schema: vol.Schema | None,
    ) -> None:
        values.update(user_input)
        if data_schema and data_schema.schema:
            for key in data_schema.schema:
                if (
                    isinstance(key, vol.Optional)
                    and key not in user_input
                    and not (
                        # don't remove advanced keys, if they are hidden
                        key.description
                        and key.description.get("advanced")
                        and not self._handler.show_advanced_options
                    )
                    and not (
                        # don't remove read_only keys
                        isinstance(data_schema.schema[key], selector.Selector)
                        and data_schema.schema[key].config.get("read_only")
                    )
                ):
                    # Key not present, delete keys old value (if present) too
                    values.pop(key.schema, None)