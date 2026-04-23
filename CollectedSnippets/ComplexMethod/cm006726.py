def _insert_field_before_action_button(self, build_config: dict, field_name: str, field_data: dict) -> None:
        """Insert a field in the correct position (before action_button) in build_config."""
        # If field already exists, don't add it again
        if field_name in build_config:
            return

        # If action_button doesn't exist, just add the field normally
        if "action_button" not in build_config:
            build_config[field_name] = field_data
            return

        # Find all the keys we need to preserve order for
        keys_before_action = []
        keys_after_action = []
        found_action = False

        for key in list(build_config.keys()):
            if key == "action_button":
                found_action = True
                keys_after_action.append(key)
            elif found_action:
                keys_after_action.append(key)
            else:
                keys_before_action.append(key)

        # Create new ordered dict
        new_config = {}

        # Add all fields before action_button
        for key in keys_before_action:
            new_config[key] = build_config[key]

        # Add the new field
        new_config[field_name] = field_data

        # Add action_button and all fields after it
        for key in keys_after_action:
            new_config[key] = build_config[key]

        # Clear and update build_config to maintain reference
        build_config.clear()
        build_config.update(new_config)