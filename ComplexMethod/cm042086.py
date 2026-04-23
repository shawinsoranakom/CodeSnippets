def test_engineer_serdeser(context):
    role = Engineer()
    ser_role_dict = role.model_dump()
    assert "name" in ser_role_dict
    assert "states" in ser_role_dict
    assert "actions" in ser_role_dict

    new_role = Engineer(**ser_role_dict)
    assert new_role.name == "Alex"
    assert new_role.use_code_review is False
    assert len(new_role.actions) == 1
    assert isinstance(new_role.actions[0], WriteCode)