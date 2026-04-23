async def test_setup_superuser_with_custom_credentials(initialized_services):  # noqa: ARG001
    """Test setup_superuser behavior with custom superuser credentials."""
    from pydantic import SecretStr

    settings = get_settings_service()
    settings.auth_settings.AUTO_LOGIN = False
    settings.auth_settings.SUPERUSER = "custom_admin"
    settings.auth_settings.SUPERUSER_PASSWORD = SecretStr("custom_password")

    # Clean DB state to avoid interference from previous tests
    async with session_scope() as session:
        # Ensure default can be removed by teardown (last_login_at must be None)
        stmt = select(User).where(User.username == DEFAULT_SUPERUSER)
        default_user = (await session.exec(stmt)).first()
        if default_user:
            default_user.last_login_at = None
            await session.commit()
            await teardown_superuser(settings, session)

        # Remove any pre-existing custom_admin user
        stmt = select(User).where(User.username == "custom_admin")
        existing_custom = (await session.exec(stmt)).first()
        if existing_custom:
            await session.delete(existing_custom)
            await session.commit()

    async with session_scope() as session:
        await setup_superuser(settings, session)

        # Verify custom superuser was created
        stmt = select(User).where(User.username == "custom_admin")
        user = (await session.exec(stmt)).first()
        assert user is not None
        assert user.is_superuser is True
        # Password should be hashed (not equal to the raw) and verify correctly
        assert user.password != "custom_password"  # noqa: S105
        assert verify_password("custom_password", user.password) is True

        # Verify default superuser was not created
        stmt = select(User).where(User.username == DEFAULT_SUPERUSER)
        default_user = (await session.exec(stmt)).first()
        assert default_user is None

        # Settings credentials should be scrubbed after setup
        assert settings.auth_settings.SUPERUSER_PASSWORD.get_secret_value() == ""

    # Cleanup: remove custom_admin to not leak state across tests
    async with session_scope() as session:
        stmt = select(User).where(User.username == "custom_admin")
        created_custom = (await session.exec(stmt)).first()
        if created_custom:
            await session.delete(created_custom)
            await session.commit()