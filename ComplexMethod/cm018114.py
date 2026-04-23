def test_cache_cleared_on_group_change() -> None:
    """Test we clear the cache when a group changes."""
    group = models.Group(
        name="Test Group", policy={"entities": {"domains": {"switch": True}}}
    )
    admin_group = models.Group(
        name="Admin group", id=models.GROUP_ID_ADMIN, policy={"entities": {}}
    )
    user = models.User(
        name="Test User", perm_lookup=None, groups=[group], is_active=True
    )
    # Make sure we cache instance
    assert user.permissions is user.permissions

    # Make sure we cache is_admin
    assert user.is_admin is user.is_admin
    assert user.is_active is True

    user.groups = []
    assert user.groups == []
    assert user.is_admin is False

    user.is_owner = True
    assert user.is_admin is True
    user.is_owner = False

    assert user.is_admin is False
    user.groups = [admin_group]
    assert user.is_admin is True

    user.is_active = False
    assert user.is_admin is False