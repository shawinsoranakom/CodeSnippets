def _merge_configs(self, *configs: RunnableConfig | None) -> RunnableConfig:
        config = super()._merge_configs(*configs)
        expected_keys = [field_spec.id for field_spec in self.history_factory_config]

        configurable = config.get("configurable", {})

        missing_keys = set(expected_keys) - set(configurable.keys())
        parameter_names = _get_parameter_names(self.get_session_history)

        if missing_keys and parameter_names:
            example_input = {self.input_messages_key: "foo"}
            example_configurable = dict.fromkeys(missing_keys, "[your-value-here]")
            example_config = {"configurable": example_configurable}
            msg = (
                f"Missing keys {sorted(missing_keys)} in config['configurable'] "
                f"Expected keys are {sorted(expected_keys)}."
                f"When using via .invoke() or .stream(), pass in a config; "
                f"e.g., chain.invoke({example_input}, {example_config})"
            )
            raise ValueError(msg)

        if len(expected_keys) == 1:
            if parameter_names:
                # If arity = 1, then invoke function by positional arguments
                message_history = self.get_session_history(
                    configurable[expected_keys[0]]
                )
            else:
                if not config:
                    config["configurable"] = {}
                message_history = self.get_session_history()
        else:
            # otherwise verify that names of keys patch and invoke by named arguments
            if set(expected_keys) != set(parameter_names):
                msg = (
                    f"Expected keys {sorted(expected_keys)} do not match parameter "
                    f"names {sorted(parameter_names)} of get_session_history."
                )
                raise ValueError(msg)

            message_history = self.get_session_history(
                **{key: configurable[key] for key in expected_keys}
            )
        config["configurable"]["message_history"] = message_history
        return config