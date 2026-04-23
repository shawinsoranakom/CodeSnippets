async def test_conversation_agent(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test OllamaConversationEntity."""
    agent = conversation.get_agent_manager(hass).async_get_agent(
        mock_config_entry.entry_id
    )
    assert agent.supported_languages == MATCH_ALL

    state = hass.states.get("conversation.ollama_conversation")
    assert state
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0

    entity_entry = entity_registry.async_get("conversation.ollama_conversation")
    assert entity_entry
    subentry = mock_config_entry.subentries.get(entity_entry.unique_id)
    assert subentry

    device_entry = device_registry.async_get(entity_entry.device_id)
    assert device_entry

    assert device_entry.identifiers == {(ollama.DOMAIN, subentry.subentry_id)}
    assert device_entry.name == subentry.title
    assert device_entry.manufacturer == "Ollama"
    assert device_entry.entry_type == dr.DeviceEntryType.SERVICE

    model, _, version = subentry.data[ollama.CONF_MODEL].partition(":")
    assert device_entry.model == model
    assert device_entry.sw_version == version