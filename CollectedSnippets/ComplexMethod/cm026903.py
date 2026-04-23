def async_get_conversation_languages(
    hass: HomeAssistant, agent_id: str | None = None
) -> set[str] | Literal["*"]:
    """Return languages supported by conversation agents.

    If an agent is specified, returns a set of languages supported by that agent.
    If no agent is specified, return a set with the union of languages supported by
    all conversation agents.
    """
    agent_manager = get_agent_manager(hass)
    agents: list[ConversationEntity | AbstractConversationAgent]

    if agent_id:
        agent = async_get_agent(hass, agent_id)

        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")

        # Shortcut
        if agent.supported_languages == MATCH_ALL:
            return MATCH_ALL

        agents = [agent]

    else:
        agents = list(hass.data[DATA_COMPONENT].entities)
        for info in agent_manager.async_get_agent_info():
            agent = agent_manager.async_get_agent(info.id)
            assert agent is not None

            # Shortcut
            if agent.supported_languages == MATCH_ALL:
                return MATCH_ALL

            agents.append(agent)

    languages: set[str] = set()

    for agent in agents:
        for language_tag in agent.supported_languages:
            languages.add(language_tag)

    return languages