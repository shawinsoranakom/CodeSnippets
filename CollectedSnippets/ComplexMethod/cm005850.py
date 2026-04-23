async def test_update_variable(service, session: AsyncSession):
    user_id = uuid4()
    name = "name"
    old_value = "old_value"
    new_value = "new_value"
    field = ""
    await service.create_variable(user_id, name, old_value, session=session)

    old_recovered = await service.get_variable(user_id, name, field, session=session)
    result = await service.update_variable(user_id, name, new_value, session=session)
    new_recovered = await service.get_variable(user_id, name, field, session=session)

    assert old_value == old_recovered
    assert new_value == new_recovered
    assert result.user_id == user_id
    assert result.name == name
    assert result.value != old_value
    assert result.value != new_value
    assert result.default_fields == []
    assert result.type == CREDENTIAL_TYPE
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime)