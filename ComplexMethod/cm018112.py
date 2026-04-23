async def test_loading_empty_data(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test we correctly load with no existing data."""
    store = auth_store.AuthStore(hass)
    await store.async_load()
    groups = await store.async_get_groups()
    assert len(groups) == 3
    admin_group = groups[0]
    assert admin_group.name == auth_store.GROUP_NAME_ADMIN
    assert admin_group.system_generated
    assert admin_group.id == auth_store.GROUP_ID_ADMIN
    user_group = groups[1]
    assert user_group.name == auth_store.GROUP_NAME_USER
    assert user_group.system_generated
    assert user_group.id == auth_store.GROUP_ID_USER
    read_group = groups[2]
    assert read_group.name == auth_store.GROUP_NAME_READ_ONLY
    assert read_group.system_generated
    assert read_group.id == auth_store.GROUP_ID_READ_ONLY

    users = await store.async_get_users()
    assert len(users) == 0