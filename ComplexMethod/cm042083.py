async def test_action_serdeser(context):
    action = Action(context=context)
    ser_action_dict = action.model_dump()
    assert "name" in ser_action_dict
    assert "llm" not in ser_action_dict  # not export
    assert "__module_class_name" in ser_action_dict

    action = Action(name="test", context=context)
    ser_action_dict = action.model_dump()
    assert "test" in ser_action_dict["name"]

    new_action = Action(**ser_action_dict, context=context)

    assert new_action.name == "test"
    assert isinstance(new_action.llm, type(context.llm()))
    assert len(await new_action._aask("who are you")) > 0