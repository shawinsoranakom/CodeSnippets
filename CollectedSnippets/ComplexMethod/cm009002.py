def test_model_request_is_frozen() -> None:
    """Test that ModelRequest raises deprecation warning on direct attribute assignment."""
    request = _make_request()
    new_model = GenericFakeChatModel(messages=iter([AIMessage(content="new model")]))

    # Direct attribute assignment should raise DeprecationWarning but still work
    with pytest.warns(
        DeprecationWarning, match="Direct attribute assignment to ModelRequest.model is deprecated"
    ):
        request.model = new_model

    # Verify the assignment actually worked
    assert request.model == new_model

    with pytest.warns(
        DeprecationWarning,
        match="Direct attribute assignment to ModelRequest.system_prompt is deprecated",
    ):
        request.system_prompt = "new prompt"  # type: ignore[misc]

    assert request.system_prompt == "new prompt"

    with pytest.warns(
        DeprecationWarning,
        match="Direct attribute assignment to ModelRequest.messages is deprecated",
    ):
        request.messages = []

    assert request.messages == []

    # Using override method should work without warnings
    request2 = _make_request()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # Turn warnings into errors
        new_request = request2.override(
            model=new_model, system_message=SystemMessage(content="override prompt")
        )

    assert new_request.model == new_model
    assert new_request.system_prompt == "override prompt"
    # Original request should be unchanged
    assert request2.model != new_model
    assert request2.system_prompt != "override prompt"