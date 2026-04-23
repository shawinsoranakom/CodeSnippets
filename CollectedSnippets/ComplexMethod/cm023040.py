async def test_ws_chat_log_subscription(
    hass: HomeAssistant,
    init_components,
    mock_conversation_input: ConversationInput,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test that we can subscribe to chat logs."""
    client = await hass_ws_client(hass)

    with freeze_time():
        now = utcnow().isoformat()

        with (
            chat_session.async_get_chat_session(hass) as session,
            async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        ):
            conversation_id = session.conversation_id
            chat_log.async_add_assistant_content_without_tools(
                AssistantContent("test-agent-id", "I hear you")
            )

        await client.send_json_auto_id(
            {
                "type": "conversation/chat_log/subscribe",
                "conversation_id": conversation_id,
            }
        )
        msg = await client.receive_json()
        assert msg["success"]
        event_id = msg["id"]

        # 1. The INITIAL_STATE event (fired before content is added)
        msg = await client.receive_json()
        assert msg == {
            "type": "event",
            "id": event_id,
            "event": {
                "event_type": "initial_state",
                "data": {
                    "conversation_id": conversation_id,
                    "continue_conversation": False,
                    "created": now,
                    "content": [
                        {"role": "system", "content": "", "created": now},
                        {"role": "user", "content": "Hello", "created": now},
                        {
                            "role": "assistant",
                            "agent_id": "test-agent-id",
                            "content": "I hear you",
                            "created": now,
                        },
                    ],
                },
            },
        }

        with (
            chat_session.async_get_chat_session(hass, conversation_id) as session,
            async_get_chat_log(hass, session, mock_conversation_input) as chat_log,
        ):
            chat_log.async_add_assistant_content_without_tools(
                AssistantContent("test-agent-id", "I still hear you")
            )

        # 2. The user input content added event
        msg = await client.receive_json()
        assert msg == {
            "type": "event",
            "id": event_id,
            "event": {
                "conversation_id": conversation_id,
                "event_type": "content_added",
                "data": {
                    "content": {
                        "content": "Hello",
                        "role": "user",
                        "created": now,
                    },
                },
            },
        }

        # 3. The assistant input content added event
        msg = await client.receive_json()
        assert msg == {
            "type": "event",
            "id": event_id,
            "event": {
                "conversation_id": conversation_id,
                "event_type": "content_added",
                "data": {
                    "content": {
                        "agent_id": "test-agent-id",
                        "content": "I still hear you",
                        "role": "assistant",
                        "created": now,
                    },
                },
            },
        }

        # Forward time to mimic auto-cleanup

        # 4. The UPDATED event (since no assistant message was added)
        msg = await client.receive_json()
        assert msg == {
            "type": "event",
            "id": event_id,
            "event": {
                "conversation_id": conversation_id,
                "event_type": "updated",
                "data": {
                    "chat_log": {
                        "continue_conversation": False,
                        "conversation_id": conversation_id,
                        "created": now,
                        "content": [
                            {
                                "content": "",
                                "role": "system",
                                "created": now,
                            },
                            {
                                "content": "Hello",
                                "role": "user",
                                "created": now,
                            },
                            {
                                "agent_id": "test-agent-id",
                                "content": "I hear you",
                                "role": "assistant",
                                "created": now,
                            },
                            {
                                "content": "Hello",
                                "role": "user",
                                "created": now,
                            },
                            {
                                "agent_id": "test-agent-id",
                                "content": "I still hear you",
                                "role": "assistant",
                                "created": now,
                            },
                        ],
                    },
                },
            },
        }

        # Trigger session cleanup
        with patch(
            "homeassistant.helpers.chat_session.CONVERSATION_TIMEOUT",
            timedelta(0),
        ):
            async_fire_time_changed(hass, fire_all=True)

        # 5. The DELETED event
        msg = await client.receive_json()
        assert msg == {
            "type": "event",
            "id": event_id,
            "event": {
                "conversation_id": conversation_id,
                "event_type": "deleted",
                "data": {},
            },
        }

        # Subscribing now will fail
        await client.send_json_auto_id(
            {
                "type": "conversation/chat_log/subscribe",
                "conversation_id": conversation_id,
            }
        )
        msg = await client.receive_json()
        assert not msg["success"]
        assert msg["error"]["code"] == "not_found"