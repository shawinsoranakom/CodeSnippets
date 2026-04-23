def execute_action(self):
        """Execute the selected Composio tool."""
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)
        composio = self._build_wrapper()
        self._populate_actions_data()
        self._build_action_maps()

        display_name = (
            self.action_button[0]["name"]
            if isinstance(getattr(self, "action_button", None), list) and self.action_button
            else self.action_button
        )
        action_key = self._display_to_key_map.get(display_name)

        if not action_key:
            msg = f"Invalid action: {display_name}"
            raise ValueError(msg)

        try:
            arguments: dict[str, Any] = {}
            param_fields = self._actions_data.get(action_key, {}).get("action_fields", [])

            schema_dict = self._action_schemas.get(action_key, {})
            parameters_schema = schema_dict.get("input_parameters", {})
            schema_properties = parameters_schema.get("properties", {}) if parameters_schema else {}
            # Handle case where 'required' field is None (causes "'NoneType' object is not iterable")
            required_list = parameters_schema.get("required", []) if parameters_schema else []
            required_fields = set(required_list) if required_list is not None else set()

            for field in param_fields:
                if not hasattr(self, field):
                    continue
                value = getattr(self, field)

                # Skip None, empty strings, and empty lists
                if value is None or value == "" or (isinstance(value, list) and len(value) == 0):
                    continue

                # Determine schema for this field
                prop_schema = schema_properties.get(field, {})

                # Parse JSON for object/array string inputs (applies to required and optional)
                if isinstance(value, str) and prop_schema.get("type") in {"array", "object"}:
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        # Fallback for simple arrays of primitives
                        if prop_schema.get("type") == "array":
                            value = [item.strip() for item in value.split(",") if item.strip() != ""]

                # For optional fields, be more strict about including them
                # Only include if the user has explicitly provided a meaningful value
                if field not in required_fields:
                    # Compare against schema default after normalization
                    schema_default = prop_schema.get("default")
                    if value == schema_default:
                        continue

                if field in self._bool_variables:
                    value = bool(value)

                # Handle renamed fields - map back to original names for API execution
                final_field_name = field
                # Check if this is a renamed reserved attribute
                if field.startswith(f"{self.app_name}_"):
                    potential_original = field[len(self.app_name) + 1 :]  # Remove app_name prefix
                    if potential_original in self.RESERVED_ATTRIBUTES:
                        final_field_name = potential_original

                arguments[final_field_name] = value

            # Get the version from the action data
            version = self._actions_data.get(action_key, {}).get("version")
            if version:
                logger.info(f"Executing {action_key} with version: {version}")

            # Execute using new SDK with version parameter
            execute_params = {
                "slug": action_key,
                "arguments": arguments,
                "user_id": self.entity_id,
            }

            # Only add version if it's available
            if version:
                execute_params["version"] = version

            result = composio.tools.execute(**execute_params)

            if isinstance(result, dict) and "successful" in result:
                if result["successful"]:
                    raw_data = result.get("data", result)
                    return self._apply_post_processor(action_key, raw_data)
                error_msg = result.get("error", "Tool execution failed")
                raise ValueError(error_msg)

        except ValueError as e:
            logger.error(f"Failed to execute {action_key}: {e}")
            raise