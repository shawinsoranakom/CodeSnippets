def test_message_serdeser():
    out_mapping = {"field3": (str, ...), "field4": (list[str], ...)}
    out_data = {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]}
    ic_obj = ActionNode.create_model_class("code", out_mapping)

    message = Message(content="code", instruct_content=ic_obj(**out_data), role="engineer", cause_by=WriteCode)
    message_dict = message.model_dump()
    assert message_dict["cause_by"] == "metagpt.actions.write_code.WriteCode"
    assert message_dict["instruct_content"] == {
        "class": "code",
        "mapping": {"field3": "(<class 'str'>, Ellipsis)", "field4": "(list[str], Ellipsis)"},
        "value": {"field3": "field3 value3", "field4": ["field4 value1", "field4 value2"]},
    }
    new_message = Message.model_validate(message_dict)
    assert new_message.content == message.content
    assert new_message.instruct_content.model_dump() == message.instruct_content.model_dump()
    assert new_message.instruct_content == message.instruct_content  # TODO
    assert new_message.cause_by == message.cause_by
    assert new_message.instruct_content.field3 == out_data["field3"]

    message = Message(content="code")
    message_dict = message.model_dump()
    new_message = Message(**message_dict)
    assert new_message.instruct_content is None
    assert new_message.cause_by == "metagpt.actions.add_requirement.UserRequirement"
    assert not Message.load("{")