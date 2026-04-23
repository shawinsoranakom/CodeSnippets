async def test_create_variable(service, session: AsyncSession):
    user_id = uuid4()
    name = "name"
    value = "value"

    result = await service.create_variable(user_id, name, value, session=session)

    assert result.user_id == user_id
    assert result.name == name
    assert result.value != value
    assert result.default_fields == []
    assert result.type == CREDENTIAL_TYPE
    assert isinstance(result.created_at, datetime)
    assert result.updated_at is None