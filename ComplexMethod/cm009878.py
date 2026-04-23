def load_agent_from_config(
    config: dict,
    llm: BaseLanguageModel | None = None,
    tools: list[Tool] | None = None,
    **kwargs: Any,
) -> BaseSingleActionAgent | BaseMultiActionAgent:
    """Load agent from Config Dict.

    Args:
        config: Config dict to load agent from.
        llm: Language model to use as the agent.
        tools: List of tools this agent has access to.
        kwargs: Additional keyword arguments passed to the agent executor.

    Returns:
        An agent executor.

    Raises:
        ValueError: If agent type is not specified in the config.
    """
    if "_type" not in config:
        msg = "Must specify an agent Type in config"
        raise ValueError(msg)
    load_from_tools = config.pop("load_from_llm_and_tools", False)
    if load_from_tools:
        if llm is None:
            msg = (
                "If `load_from_llm_and_tools` is set to True, then LLM must be provided"
            )
            raise ValueError(msg)
        if tools is None:
            msg = (
                "If `load_from_llm_and_tools` is set to True, "
                "then tools must be provided"
            )
            raise ValueError(msg)
        return _load_agent_from_tools(config, llm, tools, **kwargs)
    config_type = config.pop("_type")

    if config_type not in AGENT_TO_CLASS:
        msg = f"Loading {config_type} agent not supported"
        raise ValueError(msg)

    agent_cls = AGENT_TO_CLASS[config_type]
    if "llm_chain" in config:
        config["llm_chain"] = load_chain_from_config(config.pop("llm_chain"))
    elif "llm_chain_path" in config:
        config["llm_chain"] = load_chain(config.pop("llm_chain_path"))
    else:
        msg = "One of `llm_chain` and `llm_chain_path` should be specified."
        raise ValueError(msg)
    if "output_parser" in config:
        logger.warning(
            "Currently loading output parsers on agent is not supported, "
            "will just use the default one.",
        )
        del config["output_parser"]

    combined_config = {**config, **kwargs}
    return agent_cls(**combined_config)