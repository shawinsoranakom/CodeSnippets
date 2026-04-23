async def websocket_list_agents(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict
) -> None:
    """List conversation agents and, optionally, if they support a given language."""
    country = msg.get("country")
    language = msg.get("language")
    agents = []

    for entity in hass.data[DATA_COMPONENT].entities:
        supported_languages = entity.supported_languages
        if language and supported_languages != MATCH_ALL:
            supported_languages = language_util.matches(
                language, supported_languages, country
            )

        name = entity.entity_id
        if state := hass.states.get(entity.entity_id):
            name = state.name

        agents.append(
            {
                "id": entity.entity_id,
                "name": name,
                "supported_languages": supported_languages,
            }
        )

    manager = get_agent_manager(hass)

    for agent_info in manager.async_get_agent_info():
        agent = manager.async_get_agent(agent_info.id)
        assert agent is not None

        if isinstance(agent, ConversationEntity):
            continue

        supported_languages = agent.supported_languages
        if language and supported_languages != MATCH_ALL:
            supported_languages = language_util.matches(
                language, supported_languages, country
            )

        agent_dict: dict[str, Any] = {
            "id": agent_info.id,
            "name": agent_info.name,
            "supported_languages": supported_languages,
        }
        agents.append(agent_dict)

    connection.send_message(websocket_api.result_message(msg["id"], {"agents": agents}))