def test_environment_serdeser(context):
    out_mapping = {"field1": (list[str], ...)}
    out_data = {"field1": ["field1 value1", "field1 value2"]}
    ic_obj = ActionNode.create_model_class("prd", out_mapping)

    message = Message(
        content="prd", instruct_content=ic_obj(**out_data), role="product manager", cause_by=any_to_str(UserRequirement)
    )

    environment = Environment(context=context)
    role_c = RoleC()
    environment.add_role(role_c)
    environment.publish_message(message)

    ser_data = environment.model_dump()
    assert ser_data["roles"]["Role C"]["name"] == "RoleC"

    new_env: Environment = Environment(**ser_data, context=context)
    assert len(new_env.roles) == 1

    assert list(new_env.roles.values())[0].states == list(environment.roles.values())[0].states
    assert isinstance(list(environment.roles.values())[0].actions[0], ActionOK)
    assert type(list(new_env.roles.values())[0].actions[0]) == ActionOK
    assert type(list(new_env.roles.values())[0].actions[1]) == ActionRaise
    assert list(new_env.roles.values())[0].rc.watch == role_c.rc.watch