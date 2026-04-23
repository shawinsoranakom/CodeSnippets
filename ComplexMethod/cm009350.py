def test_chat_groq_extra_kwargs() -> None:
    """Test extra kwargs to chat groq."""
    # Check that foo is saved in extra_kwargs.
    with pytest.warns(UserWarning) as record:
        llm = ChatGroq(model="foo", foo=3, max_tokens=10)  # type: ignore[call-arg]
        assert llm.max_tokens == 10
        assert llm.model_kwargs == {"foo": 3}
    assert len(record) == 1
    assert type(record[0].message) is UserWarning
    assert "foo is not default parameter" in record[0].message.args[0]

    # Test that if extra_kwargs are provided, they are added to it.
    with pytest.warns(UserWarning) as record:
        llm = ChatGroq(model="foo", foo=3, model_kwargs={"bar": 2})  # type: ignore[call-arg]
        assert llm.model_kwargs == {"foo": 3, "bar": 2}
    assert len(record) == 1
    assert type(record[0].message) is UserWarning
    assert "foo is not default parameter" in record[0].message.args[0]

    # Test that if provided twice it errors
    with pytest.raises(ValueError):
        ChatGroq(model="foo", foo=3, model_kwargs={"foo": 2})  # type: ignore[call-arg]

    # Test that if explicit param is specified in kwargs it errors
    with pytest.raises(ValueError):
        ChatGroq(model="foo", model_kwargs={"temperature": 0.2})

    # Test that "model" cannot be specified in kwargs
    with pytest.raises(ValueError):
        ChatGroq(model="foo", model_kwargs={"model": "test-model"})