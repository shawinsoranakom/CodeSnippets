def _process_direct_type_field(
        self, field_name: str, field: dict, params: dict[str, Any], load_from_db_fields: list[str]
    ) -> tuple[dict[str, Any], list[str]]:
        """Process direct type fields."""
        val = field.get("value")

        if field.get("type") == "code":
            params = self._handle_code_field(field_name, val, params)
        elif field.get("type") in {"dict", "NestedDict"}:
            params = self._handle_dict_field(field_name, val, params)
        elif field.get("type") == "table":
            params = self._handle_table_field(field_name, val, params, load_from_db_fields)
        else:
            params = self._handle_other_direct_types(field_name, field, val, params)

        if field.get("load_from_db"):
            # Skip load_from_db if the field itself has an incoming edge
            has_incoming_edge = self.vertex.get_incoming_edge_by_target_param(field_name) is not None
            # Skip credential fields when the model field has an incoming edge,
            # because the connected model component provides its own credentials
            is_secret = field.get("_input_type") == "SecretStrInput" or field.get("password")
            model_has_edge = (
                is_secret
                and "model" in self.template_dict
                and self.vertex.get_incoming_edge_by_target_param("model") is not None
            )
            # Skip credential fields when the node is in "Connect other models" mode
            # (user chose to wire an external model instead of the built-in provider)
            model_field = self.template_dict.get("model", {})
            in_connection_mode = is_secret and model_field.get("_connection_mode", False)
            if not has_incoming_edge and not model_has_edge and not in_connection_mode:
                load_from_db_fields.append(field_name)

        return params, load_from_db_fields