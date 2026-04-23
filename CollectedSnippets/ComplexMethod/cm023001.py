async def test_custom_agent(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_admin_user: MockUser,
    mock_conversation_agent: MockAgent,
    snapshot: SnapshotAssertion,
) -> None:
    """Test a custom conversation agent."""
    client = await hass_client()

    data = {
        "text": "Test Text",
        "conversation_id": "test-conv-id",
        "language": "test-language",
        "agent_id": mock_conversation_agent.agent_id,
    }

    resp = await client.post("/api/conversation/process", json=data)
    assert resp.status == HTTPStatus.OK
    data = await resp.json()
    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"
    assert data["response"]["speech"]["plain"]["speech"] == "Test response"
    assert data["conversation_id"] == "test-conv-id"

    assert len(mock_conversation_agent.calls) == 1
    assert mock_conversation_agent.calls[0].text == "Test Text"
    assert mock_conversation_agent.calls[0].context.user_id == hass_admin_user.id
    assert mock_conversation_agent.calls[0].conversation_id == "test-conv-id"
    assert mock_conversation_agent.calls[0].language == "test-language"

    conversation.async_unset_agent(
        hass, hass.config_entries.async_get_entry(mock_conversation_agent.agent_id)
    )