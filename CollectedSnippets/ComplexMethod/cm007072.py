def update_build_config(self, build_config: dotdict, field_value: Any, field_name: str | None = None) -> dotdict:
        if field_name == "operations":
            build_config["operations"]["value"] = field_value
            # Mirror Text Operations: first hide all operation-specific fields and clear their values
            for field in self.ALL_OPERATION_FIELDS:
                if field in build_config:
                    build_config[field]["show"] = False
                    if field in self.OPERATION_FIELD_DEFAULTS:
                        build_config[field]["value"] = self.OPERATION_FIELD_DEFAULTS[field]

            selected_actions = [
                action["name"] for action in (field_value or []) if isinstance(action, dict) and "name" in action
            ]
            if len(selected_actions) == 1 and selected_actions[0] in ACTION_CONFIG:
                action = selected_actions[0]
                config = ACTION_CONFIG[action]
                build_config["data"]["is_list"] = config["is_list"]
                logger.info(config["log_msg"])
                return set_current_fields(
                    build_config=build_config,
                    action_fields=self.actions_data,
                    selected_action=action,
                    default_fields=["operations", "data"],
                    func=set_field_display,
                )
            return build_config

        if field_name == "mapped_json_display":
            try:
                parsed_json = json.loads(field_value)
                keys = DataOperationsComponent.extract_all_paths(parsed_json)
                build_config["selected_key"]["options"] = keys
                build_config["selected_key"]["show"] = True
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.error(f"Error parsing mapped JSON: {e}")
                build_config["selected_key"]["show"] = False

        return build_config