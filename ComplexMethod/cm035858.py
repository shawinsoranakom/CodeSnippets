async def require_financial_data_access(
    request: Request,
    org_id: UUID,
    user_id: str | None = Depends(get_user_id),
) -> str:
    """
    Authorization dependency for accessing organization financial data.

    Allows access if ANY of these conditions are met:
    1. User has Admin or Owner role in the organization
    2. User has @openhands.dev email domain

    This is used for the organization members financial data endpoint.

    Args:
        request: FastAPI request object
        org_id: Organization UUID from path parameter
        user_id: User ID from authentication

    Returns:
        str: User ID if authorized

    Raises:
        HTTPException: 401 if not authenticated, 403 if not authorized
    """
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='User not authenticated',
        )

    # Validate API key organization binding
    api_key_org_id = await get_api_key_org_id_from_request(request)
    if api_key_org_id is not None:
        if api_key_org_id != org_id:
            logger.warning(
                'API key organization mismatch for financial data access',
                extra={
                    'user_id': user_id,
                    'api_key_org_id': str(api_key_org_id),
                    'target_org_id': str(org_id),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='API key is not authorized for this organization',
            )

    # Check if user has @openhands.dev email
    user_auth = await get_user_auth(request)
    user_email = await user_auth.get_user_email()

    if user_email and user_email.endswith('@openhands.dev'):
        logger.debug(
            'Financial data access granted via @openhands.dev email',
            extra={'user_id': user_id, 'org_id': str(org_id)},
        )
        return user_id

    # Check if user has Admin or Owner role in the organization
    user_role = await get_user_org_role(user_id, org_id)

    if not user_role:
        logger.warning(
            'Financial data access denied - user not a member of organization',
            extra={'user_id': user_id, 'org_id': str(org_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='User is not a member of this organization',
        )

    if user_role.name not in (RoleName.OWNER.value, RoleName.ADMIN.value):
        logger.warning(
            'Financial data access denied - insufficient role',
            extra={
                'user_id': user_id,
                'org_id': str(org_id),
                'user_role': user_role.name,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access restricted to organization admins, owners, or OpenHands members',
        )

    logger.debug(
        'Financial data access granted via admin/owner role',
        extra={'user_id': user_id, 'org_id': str(org_id), 'role': user_role.name},
    )
    return user_id