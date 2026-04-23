async def _create_superuser(username: str, password: str, auth_token: str | None):
    """Create a superuser."""
    await initialize_services()

    settings_service = get_settings_service()
    # Check if superuser creation via CLI is enabled
    if not settings_service.auth_settings.ENABLE_SUPERUSER_CLI:
        typer.echo("Error: Superuser creation via CLI is disabled.")
        typer.echo("Set LANGFLOW_ENABLE_SUPERUSER_CLI=true to enable this feature.")
        raise typer.Exit(1)

    if settings_service.auth_settings.AUTO_LOGIN:
        # Force default credentials for AUTO_LOGIN mode
        username = DEFAULT_SUPERUSER
        password = DEFAULT_SUPERUSER_PASSWORD.get_secret_value()
    else:
        # Production mode - prompt for credentials if not provided
        if not username:
            username = typer.prompt("Username")
        if not password:
            password = typer.prompt("Password", hide_input=True)

    from langflow.services.database.models.user.crud import get_all_superusers

    existing_superusers = []
    async with session_scope() as session:
        # Note that the default superuser is created by the initialize_services() function,
        # but leaving this check here in case we change that behavior
        existing_superusers = await get_all_superusers(session)
    is_first_setup = len(existing_superusers) == 0

    # If AUTO_LOGIN is true, only allow default superuser creation
    if settings_service.auth_settings.AUTO_LOGIN:
        if not is_first_setup:
            typer.echo("Error: Cannot create additional superusers when AUTO_LOGIN is enabled.")
            typer.echo("AUTO_LOGIN mode is for development with only the default superuser.")
            typer.echo("To create additional superusers:")
            typer.echo("1. Set LANGFLOW_AUTO_LOGIN=false")
            typer.echo("2. Run this command again with --auth-token")
            raise typer.Exit(1)

        typer.echo(f"AUTO_LOGIN enabled. Creating default superuser '{username}'...")
        # Do not echo the default password to avoid exposing it in logs.
    # AUTO_LOGIN is false - production mode
    elif is_first_setup:
        typer.echo("No superusers found. Creating first superuser...")
    else:
        # Authentication is required in production mode
        if not auth_token:
            typer.echo("Error: Creating a superuser requires authentication.")
            typer.echo("Please provide --auth-token with a valid superuser API key or JWT token.")
            typer.echo("To get a token, use: `uv run langflow api_key`")
            raise typer.Exit(1)

        # Validate the auth token
        try:
            auth_user = None
            async with session_scope() as session:
                # Try JWT first
                user = None
                try:
                    user = await get_current_user_from_access_token(auth_token, session)
                except (InvalidTokenError, HTTPException):
                    # Try API key
                    api_key_result = await check_key(session, auth_token)
                    if api_key_result and hasattr(api_key_result, "is_superuser"):
                        user = api_key_result
                auth_user = user

            if not auth_user or not auth_user.is_superuser:
                typer.echo(
                    "Error: Invalid token or insufficient privileges. Only superusers can create other superusers."
                )
                raise typer.Exit(1)
        except typer.Exit:
            raise  # Re-raise typer.Exit without wrapping
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Error: Authentication failed - {e!s}")
            raise typer.Exit(1) from None

    # Auth complete, create the superuser
    async with session_scope() as session:
        from langflow.services.deps import get_auth_service

        auth = get_auth_service()
        if await auth.create_super_user(username, password, db=session):
            # Verify that the superuser was created
            from langflow.services.database.models.user.model import User

            stmt = select(User).where(User.username == username)
            created_user: User = (await session.exec(stmt)).first()
            if created_user is None or not created_user.is_superuser:
                typer.echo("Superuser creation failed.")
                return
            # Now create the first folder for the user
            result = await get_or_create_default_folder(session, created_user.id)
            if result:
                typer.echo("Default folder created successfully.")
            else:
                msg = "Could not create default folder."
                raise RuntimeError(msg)

            # Log the superuser creation for audit purposes
            logger.warning(
                f"SECURITY AUDIT: New superuser '{username}' created via CLI command"
                + (" by authenticated user" if auth_token else " (first-time setup)")
            )
            typer.echo("Superuser created successfully.")

        else:
            logger.error(f"SECURITY AUDIT: Failed attempt to create superuser '{username}' via CLI")
            typer.echo("Superuser creation failed.")