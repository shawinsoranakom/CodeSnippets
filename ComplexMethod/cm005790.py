def test_convert_to_langchain(method_name):
    def convert(value):
        if method_name == "message":
            return value.to_lc_message()
        if method_name == "convert_to_langchain_type":
            return convert_to_langchain_type(value)
        msg = f"Invalid method: {method_name}"
        raise ValueError(msg)

    lc_message = convert(Message(text="Test message 1", sender="User", sender_name="User", session_id="session_id2"))
    assert lc_message.content == "Test message 1"
    assert lc_message.type == "human"

    lc_message = convert(Message(text="Test message 2", sender="AI", session_id="session_id2"))
    assert lc_message.content == "Test message 2"
    assert lc_message.type == "ai"

    iterator = iter(["stream", "message"])
    lc_message = convert(Message(text=iterator, sender="AI", session_id="session_id2"))
    assert lc_message.content == ""
    assert lc_message.type == "ai"
    expected_len = 2
    assert len(list(iterator)) == expected_len