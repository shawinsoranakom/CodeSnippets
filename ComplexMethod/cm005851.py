async def test_update_variable_fields(service, session: AsyncSession):
    user_id = uuid4()
    new_name = new_value = "donkey"
    variable = await service.create_variable(user_id, "old_name", "old_value", session=session)
    saved = variable.model_dump()
    variable = VariableUpdate(**saved)
    variable.name = new_name
    variable.value = new_value
    variable.default_fields = ["new_field"]

    result = await service.update_variable_fields(
        user_id=user_id,
        variable_id=saved.get("id"),
        variable=variable,
        session=session,
    )

    assert result.name == new_name
    assert result.value != new_value
    assert saved.get("id") == result.id
    assert saved.get("user_id") == result.user_id
    assert saved.get("name") != result.name
    assert saved.get("value") != result.value
    assert saved.get("default_fields") != result.default_fields
    assert saved.get("type") == result.type
    assert saved.get("created_at") == result.created_at
    assert saved.get("updated_at") != result.updated_at