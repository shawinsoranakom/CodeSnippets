def test_message_factory() -> None:
    factory = MessageFactory()

    # Text message data
    text_data = {
        "type": "TextMessage",
        "source": "test_agent",
        "content": "Hello, world!",
    }

    # Create a TextMessage instance
    text_message = factory.create(text_data)
    assert isinstance(text_message, TextMessage)
    assert text_message.source == "test_agent"
    assert text_message.content == "Hello, world!"
    assert text_message.type == "TextMessage"  # type: ignore[comparison-overlap]

    # Handoff message data
    handoff_data = {
        "type": "HandoffMessage",
        "source": "test_agent",
        "content": "handoff to another agent",
        "target": "target_agent",
    }

    # Create a HandoffMessage instance
    handoff_message = factory.create(handoff_data)
    assert isinstance(handoff_message, HandoffMessage)
    assert handoff_message.source == "test_agent"
    assert handoff_message.content == "handoff to another agent"
    assert handoff_message.target == "target_agent"
    assert handoff_message.type == "HandoffMessage"  # type: ignore[comparison-overlap]

    # Structured message data
    structured_data = {
        "type": "StructuredMessage[TestContent]",
        "source": "test_agent",
        "content": {
            "field1": "test",
            "field2": 42,
        },
    }
    # Create a StructuredMessage instance -- this will fail because the type
    # is not registered in the factory.
    with pytest.raises(ValueError):
        structured_message = factory.create(structured_data)
    # Register the StructuredMessage type in the factory
    factory.register(StructuredMessage[TestContent])
    # Create a StructuredMessage instance
    structured_message = factory.create(structured_data)
    assert isinstance(structured_message, StructuredMessage)
    assert isinstance(structured_message.content, TestContent)  # type: ignore[reportUnkownMemberType]
    assert structured_message.source == "test_agent"
    assert structured_message.content.field1 == "test"
    assert structured_message.content.field2 == 42
    assert structured_message.type == "StructuredMessage[TestContent]"  # type: ignore[comparison-overlap]

    sm_factory = StructuredMessageFactory(input_model=TestContent, format_string=None, content_model_name="TestContent")
    config = sm_factory.dump_component()
    config.config["content_model_name"] = "DynamicTestContent"
    sm_factory_dynamic = StructuredMessageFactory.load_component(config)

    factory.register(sm_factory_dynamic.StructuredMessage)
    msg = sm_factory_dynamic.StructuredMessage(
        content=sm_factory_dynamic.ContentModel(field1="static", field2=123), source="static_agent"
    )
    restored = factory.create(msg.dump())
    assert isinstance(restored, StructuredMessage)
    assert isinstance(restored.content, sm_factory_dynamic.ContentModel)  # type: ignore[reportUnkownMemberType]
    assert restored.source == "static_agent"
    assert restored.content.field1 == "static"  # type: ignore[attr-defined]
    assert restored.content.field2 == 123