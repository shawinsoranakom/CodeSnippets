async def initialize_agentic_global_variables(session: AsyncSession) -> None:
    """Initialize default global variables for agentic experience for all users.

    This function creates agentic-specific global variables (FLOW_ID, COMPONENT_ID, FIELD_NAME)
    for all users if they don't already exist. These variables are used by the agentic
    experience to provide context-aware suggestions and operations.

    Args:
        session: Database session for querying users and creating variables.
    """
    settings_service = get_settings_service()

    # Only initialize if agentic experience is enabled
    if not settings_service.settings.agentic_experience:
        await logger.adebug("Agentic experience disabled, skipping agentic variables initialization")
        return

    await logger.ainfo("Initializing agentic global variables for all users...")

    try:
        # Get all users in the system
        users = (await session.exec(select(User))).all()
        await logger.adebug(f"Found {len(users)} users for agentic variables initialization")

        if not users:
            await logger.adebug("No users found, skipping agentic variables initialization")
            return

        variable_service = get_variable_service()

        # Define agentic variables with default values
        agentic_variables = {
            "FLOW_ID": "",
            "COMPONENT_ID": "",
            "FIELD_NAME": "",
        }

        # Initialize variables for each user
        variables_created = 0
        variables_skipped = 0

        for user in users:
            try:
                await logger.adebug(f"Initializing agentic variables for user: {user.username}")

                # Get existing variables for this user
                existing_vars = await variable_service.list_variables(user.id, session)

                for var_name, default_value in agentic_variables.items():
                    try:
                        if var_name not in existing_vars:
                            # Create variable with default value
                            await variable_service.create_variable(
                                user_id=user.id,
                                name=var_name,
                                value=default_value,
                                default_fields=[],
                                type_=GENERIC_TYPE,
                                session=session,
                            )
                            variables_created += 1
                            await logger.adebug(f"Created agentic variable {var_name} for user {user.username}")
                        else:
                            variables_skipped += 1
                            await logger.adebug(
                                f"Agentic variable {var_name} already exists for user {user.username}, skipping"
                            )
                    except (
                        HTTPException,
                        sqlalchemy_exc.SQLAlchemyError,
                        OSError,
                        PermissionError,
                        FileNotFoundError,
                        RuntimeError,
                        ValueError,
                        AttributeError,
                    ) as e:
                        await logger.aexception(
                            f"Error creating agentic variable {var_name} for user {user.username}: {e}"
                        )
                        continue

            except (
                HTTPException,
                sqlalchemy_exc.SQLAlchemyError,
                OSError,
                PermissionError,
                FileNotFoundError,
                RuntimeError,
                ValueError,
                AttributeError,
            ) as e:
                await logger.aexception(f"Failed to initialize agentic variables for user {user.username}: {e}")
                continue

        await logger.ainfo(
            f"Agentic variables initialization complete: {variables_created} created, {variables_skipped} skipped"
        )

    except (
        HTTPException,
        sqlalchemy_exc.SQLAlchemyError,
        OSError,
        PermissionError,
        FileNotFoundError,
        RuntimeError,
        ValueError,
        AttributeError,
    ) as e:
        await logger.aexception(f"Error during agentic variables initialization: {e}")