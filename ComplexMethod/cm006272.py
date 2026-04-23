async def get_or_create_super_user(session: AsyncSession, username, password, is_default):
    from langflow.services.database.models.user.model import User

    stmt = select(User).where(User.username == username)
    result = await session.exec(stmt)
    user = result.first()

    auth = get_auth_service()
    if user and user.is_superuser:
        return None  # Superuser already exists

    if user and is_default:
        if user.is_superuser:
            if auth.verify_password(password, user.password):
                return None
            # Superuser exists but password is incorrect
            # which means that the user has changed the
            # base superuser credentials.
            # This means that the user has already created
            # a superuser and changed the password in the UI
            # so we don't need to do anything.
            await logger.adebug(
                "Superuser exists but password is incorrect. "
                "This means that the user has changed the "
                "base superuser credentials."
            )
            return None
        logger.debug("User with superuser credentials exists but is not a superuser.")
        return None

    if user:
        if auth.verify_password(password, user.password):
            msg = "User with superuser credentials exists but is not a superuser."
            raise ValueError(msg)
        msg = "Incorrect superuser credentials"
        raise ValueError(msg)

    if is_default:
        logger.debug("Creating default superuser.")
    else:
        logger.debug("Creating superuser.")
    return await auth.create_super_user(username, password, db=session)