def test_setting_service_tier_request() -> None:
    """Test setting service tier defined at request level."""
    message = HumanMessage(content="Welcome to the Groqetship")
    chat = ChatGroq(model=DEFAULT_MODEL_NAME)

    response = chat.invoke(
        [message],
        service_tier="auto",
    )
    assert isinstance(response, BaseMessage)
    assert isinstance(response.content, str)
    assert response.response_metadata.get("service_tier") == "auto"

    response = chat.invoke(
        [message],
        service_tier="flex",
    )
    assert response.response_metadata.get("service_tier") == "flex"

    response = chat.invoke(
        [message],
        service_tier="on_demand",
    )
    assert response.response_metadata.get("service_tier") == "on_demand"

    assert chat.service_tier == "on_demand"
    response = chat.invoke(
        [message],
    )
    assert response.response_metadata.get("service_tier") == "on_demand"

    # If an `invoke` call is made with no service tier, we fall back to the class level
    # setting
    chat = ChatGroq(model=DEFAULT_MODEL_NAME, service_tier="auto")
    response = chat.invoke(
        [message],
    )
    assert response.response_metadata.get("service_tier") == "auto"

    response = chat.invoke(
        [message],
        service_tier="on_demand",
    )
    assert response.response_metadata.get("service_tier") == "on_demand"

    with pytest.raises(BadRequestError):
        response = chat.invoke(
            [message],
            service_tier="invalid",
        )

    response = chat.invoke(
        [message],
        service_tier=None,
    )
    assert response.response_metadata.get("service_tier") == "auto"