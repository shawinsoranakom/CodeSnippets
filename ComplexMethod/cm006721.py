def _update_action_config(self, build_config: dict, selected_value: Any) -> None:
        """Add or update parameter input fields for the chosen action."""
        if not selected_value:
            return

        # The UI passes either a list with dict [{name: display_name}] OR the raw key
        if isinstance(selected_value, list) and selected_value:
            display_name = selected_value[0]["name"]
        else:
            display_name = selected_value

        action_key = self.desanitize_action_name(display_name)

        # Skip validation for default/placeholder values
        if action_key in ("disabled", "placeholder", ""):
            logger.debug(f"Skipping action config update for placeholder value: {action_key}")
            return

        lf_inputs = self._validate_schema_inputs(action_key)

        # First remove inputs belonging to other actions
        self._remove_inputs_from_build_config(build_config, action_key)

        # Add / update the inputs for this action
        for inp in lf_inputs:
            if inp.name is not None:
                inp_dict = inp.to_dict() if hasattr(inp, "to_dict") else inp.__dict__.copy()

                # Do not mutate input_types here; keep original configuration

                inp_dict.setdefault("show", True)  # visible once action selected
                # Preserve previously entered value if user already filled something
                if inp.name in build_config:
                    existing_val = build_config[inp.name].get("value")
                    inp_dict.setdefault("value", existing_val)
                build_config[inp.name] = inp_dict

        # Ensure _all_fields includes new ones
        self._all_fields.update({i.name for i in lf_inputs if i.name is not None})

        # Normalize input_types to prevent None values
        self.update_input_types(build_config)