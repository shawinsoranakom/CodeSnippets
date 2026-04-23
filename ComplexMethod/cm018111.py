async def test_loading_all_access_group_data_format(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test we correctly load old data with single group."""
    hass_storage[auth_store.STORAGE_KEY] = MOCK_STORAGE_DATA

    store = auth_store.AuthStore(hass)
    await store.async_load()
    groups = await store.async_get_groups()
    assert len(groups) == 3
    admin_group = groups[0]
    assert admin_group.name == auth_store.GROUP_NAME_ADMIN
    assert admin_group.system_generated
    assert admin_group.id == auth_store.GROUP_ID_ADMIN
    read_group = groups[1]
    assert read_group.name == auth_store.GROUP_NAME_READ_ONLY
    assert read_group.system_generated
    assert read_group.id == auth_store.GROUP_ID_READ_ONLY
    user_group = groups[2]
    assert user_group.name == auth_store.GROUP_NAME_USER
    assert user_group.system_generated
    assert user_group.id == auth_store.GROUP_ID_USER

    users = await store.async_get_users()
    assert len(users) == 2

    owner, system = users

    assert owner.system_generated is False
    assert owner.groups == [admin_group]
    assert len(owner.refresh_tokens) == 1
    owner_token = list(owner.refresh_tokens.values())[0]
    assert owner_token.id == "user-token-id"
    assert owner_token.version == "1.2.3"

    assert system.system_generated is True
    assert system.groups == []
    assert len(system.refresh_tokens) == 1
    system_token = list(system.refresh_tokens.values())[0]
    assert system_token.id == "system-token-id"
    assert system_token.version is None