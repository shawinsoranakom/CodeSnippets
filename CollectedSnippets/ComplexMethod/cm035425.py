def from_toml_section(cls, data: dict) -> dict[str, AgentConfig]:
        """Create a mapping of AgentConfig instances from a toml dictionary representing the [agent] section.

        The default configuration is built from all non-dict keys in data.
        Then, each key with a dict value is treated as a custom agent configuration, and its values override
        the default configuration.

        Example:
        Apply generic agent config with custom agent overrides, e.g.
            [agent]
            enable_prompt_extensions = false
            [agent.BrowsingAgent]
            enable_prompt_extensions = true
        results in prompt_extensions being true for BrowsingAgent but false for others.

        Returns:
            dict[str, AgentConfig]: A mapping where the key "agent" corresponds to the default configuration
            and additional keys represent custom configurations.
        """
        # Initialize the result mapping
        agent_mapping: dict[str, AgentConfig] = {}

        # Extract base config data (non-dict values)
        base_data = {}
        custom_sections: dict[str, dict] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                custom_sections[key] = value
            else:
                base_data[key] = value

        # Try to create the base config
        try:
            base_config = cls.model_validate(base_data)
            agent_mapping['agent'] = base_config
        except ValidationError as e:
            logger.warning(f'Invalid base agent configuration: {e}. Using defaults.')
            # If base config fails, create a default one
            base_config = cls()
            # Still add it to the mapping
            agent_mapping['agent'] = base_config

        # Process each custom section independently
        for name, overrides in custom_sections.items():
            try:
                # Merge base config with overrides
                merged = {**base_config.model_dump(), **overrides}
                if merged.get('classpath'):
                    # if an explicit classpath is given, try to load it and look up its config model class
                    from openhands.controller.agent import Agent

                    try:
                        agent_cls = get_impl(Agent, merged.get('classpath'))
                        custom_config = agent_cls.config_model.model_validate(merged)
                    except Exception as e:
                        logger.warning(
                            f'Failed to load custom agent class [{merged.get("classpath")}]: {e}. Using default config model.'
                        )
                        custom_config = cls.model_validate(merged)
                else:
                    # otherwise, try to look up the agent class by name (i.e. if it's a built-in)
                    # if that fails, just use the default AgentConfig class.
                    try:
                        agent_cls = Agent.get_cls(name)
                        custom_config = agent_cls.config_model.model_validate(merged)
                    except Exception:
                        # otherwise, just fall back to the default config model
                        custom_config = cls.model_validate(merged)
                agent_mapping[name] = custom_config
            except ValidationError as e:
                logger.warning(
                    f'Invalid agent configuration for [{name}]: {e}. This section will be skipped.'
                )
                # Skip this custom section but continue with others
                continue

        return agent_mapping