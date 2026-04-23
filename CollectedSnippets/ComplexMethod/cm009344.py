def test_setting_service_tier_class() -> None:
    """Test setting service tier defined at ChatGroq level."""
    message = HumanMessage(content="Welcome to the Groqetship")

    # Initialization
    chat = ChatGroq(model=DEFAULT_MODEL_NAME, service_tier="auto")
    assert chat.service_tier == "auto"
    response = chat.invoke([message])
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)
    assert response.response_metadata.get("service_tier") == "auto"

    chat = ChatGroq(model=DEFAULT_MODEL_NAME, service_tier="flex")
    assert chat.service_tier == "flex"
    response = chat.invoke([message])
    assert response.response_metadata.get("service_tier") == "flex"

    chat = ChatGroq(model=DEFAULT_MODEL_NAME, service_tier="on_demand")
    assert chat.service_tier == "on_demand"
    response = chat.invoke([message])
    assert response.response_metadata.get("service_tier") == "on_demand"

    chat = ChatGroq(model=DEFAULT_MODEL_NAME)
    assert chat.service_tier == "on_demand"
    response = chat.invoke([message])
    assert response.response_metadata.get("service_tier") == "on_demand"

    with pytest.raises(ValueError):
        ChatGroq(model=DEFAULT_MODEL_NAME, service_tier=None)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        ChatGroq(model=DEFAULT_MODEL_NAME, service_tier="invalid")