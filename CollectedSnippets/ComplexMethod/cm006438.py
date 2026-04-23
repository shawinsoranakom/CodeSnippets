async def verify_project_auth(
    db: AsyncSession,
    project_id: UUID,
    query_param: str,
    header_param: str,
) -> User:
    """MCP-specific user authentication that allows fallback to username lookup when not using API key auth.

    This function provides authentication for MCP endpoints when using MCP Composer and no API key is provided,
    or checks if the API key is valid.
    """
    settings_service = get_settings_service()
    result: ApiKey | User | None

    project = (await db.exec(select(Folder).where(Folder.id == project_id))).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    auth_settings: AuthSettings | None = None
    # Check if this project requires API key only authentication
    if project.auth_settings:
        auth_settings = AuthSettings(**project.auth_settings)

    if (not auth_settings and not settings_service.auth_settings.AUTO_LOGIN) or (
        auth_settings and auth_settings.auth_type == "apikey"
    ):
        api_key = query_param or header_param
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="API key required for this project. Provide x-api-key header or query parameter.",
            )

        # Validate the API key
        user = await check_key(db, api_key)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Verify user has access to the project
        project_access = (
            await db.exec(select(Folder).where(Folder.id == project_id, Folder.user_id == user.id))
        ).first()

        if not project_access:
            raise HTTPException(status_code=404, detail="Project not found")

        return user

    # Get the first user
    if not settings_service.auth_settings.SUPERUSER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing superuser username in auth settings",
        )
    # For MCP endpoints, always fall back to username lookup when no API key is provided
    result = await get_user_by_username(db, settings_service.auth_settings.SUPERUSER)
    if result:
        logger.warning(AUTO_LOGIN_WARNING)
        return result
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid user",
    )