def test_message_serdeser_from_create_model():
    with pytest.raises(KeyError):
        _ = Message(content="code", instruct_content={"class": "test", "key": "value"})

    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)
    ic_inst = ic_obj(**out_data)

    message = Message(content="code", instruct_content=ic_inst, role="engineer", cause_by=WriteCode)
    ser_data = message.model_dump()
    assert ser_data["cause_by"] == "metagpt.actions.write_code.WriteCode"
    assert ser_data["instruct_content"]["class"] == "code"

    new_message = Message(**ser_data)
    assert new_message.cause_by == any_to_str(WriteCode)
    assert new_message.cause_by in [any_to_str(WriteCode)]

    assert new_message.instruct_content == ic_obj(**out_data)
    assert new_message.instruct_content == ic_inst
    assert new_message.instruct_content.model_dump() == ic_obj(**out_data).model_dump()
    assert new_message == message

    mock_msg = MockMessage()
    message = Message(content="test_ic", instruct_content=mock_msg)
    ser_data = message.model_dump()
    new_message = Message(**ser_data)
    assert new_message.instruct_content == mock_msg
    assert new_message == message