async def setup_superuser(settings_service: SettingsService, session: AsyncSession) -> None:
    if settings_service.auth_settings.AUTO_LOGIN:
        await logger.adebug("AUTO_LOGIN is set to True. Creating default superuser.")
        username = DEFAULT_SUPERUSER
        password = DEFAULT_SUPERUSER_PASSWORD.get_secret_value()
    else:
        # Remove the default superuser if it exists
        await teardown_superuser(settings_service, session)
        # If AUTO_LOGIN is disabled, attempt to use configured credentials
        # or fall back to default credentials if none are provided.
        username = settings_service.auth_settings.SUPERUSER or DEFAULT_SUPERUSER
        password = (settings_service.auth_settings.SUPERUSER_PASSWORD or DEFAULT_SUPERUSER_PASSWORD).get_secret_value()

    if not username or not password:
        msg = "Username and password must be set"
        raise ValueError(msg)

    is_default = (username == DEFAULT_SUPERUSER) and (password == DEFAULT_SUPERUSER_PASSWORD.get_secret_value())

    try:
        user = await get_or_create_super_user(
            session=session, username=username, password=password, is_default=is_default
        )
        if user is not None:
            await logger.adebug("Superuser created successfully.")
    except Exception as exc:
        logger.exception(exc)
        msg = "Could not create superuser. Please create a superuser manually."
        raise RuntimeError(msg) from exc
    finally:
        # Scrub credentials from in-memory settings after setup
        settings_service.auth_settings.reset_credentials()