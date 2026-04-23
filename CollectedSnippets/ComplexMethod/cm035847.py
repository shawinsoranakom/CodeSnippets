async def accept_invitation(
    request_data: AcceptInvitationRequest,
    user_id: str = Depends(get_user_id),
):
    """Accept an organization invitation via authenticated POST request.

    This endpoint is called by the frontend after displaying the acceptance modal.
    Requires authentication - cookies are sent because this is a same-origin request.

    Args:
        request_data: Contains the invitation token
        user_id: Authenticated user ID (from dependency)

    Returns:
        AcceptInvitationResponse: Success response with organization details

    Raises:
        HTTPException 400: Invalid or expired token
        HTTPException 403: Email mismatch
        HTTPException 409: User already a member
    """
    token = request_data.token

    try:
        invitation = await OrgInvitationService.accept_invitation(token, UUID(user_id))

        # Get organization and role details for response
        org = await OrgStore.get_org_by_id(invitation.org_id)
        role = await RoleStore.get_role_by_id(invitation.role_id)

        logger.info(
            'Invitation accepted via API',
            extra={
                'token_prefix': token[:10] + '...',
                'user_id': user_id,
                'org_id': str(invitation.org_id),
            },
        )

        return AcceptInvitationResponse(
            success=True,
            org_id=str(invitation.org_id),
            org_name=org.name if org else '',
            role=role.name if role else '',
        )

    except InvitationExpiredError:
        logger.warning(
            'Invitation accept failed: expired',
            extra={'token_prefix': token[:10] + '...', 'user_id': user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='invitation_expired',
        )

    except InvitationInvalidError as e:
        logger.warning(
            'Invitation accept failed: invalid',
            extra={
                'token_prefix': token[:10] + '...',
                'user_id': user_id,
                'error': str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='invitation_invalid',
        )

    except UserAlreadyMemberError:
        logger.info(
            'Invitation accept: user already member',
            extra={'token_prefix': token[:10] + '...', 'user_id': user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='already_member',
        )

    except EmailMismatchError as e:
        logger.warning(
            'Invitation accept failed: email mismatch',
            extra={
                'token_prefix': token[:10] + '...',
                'user_id': user_id,
                'error': str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='email_mismatch',
        )

    except Exception as e:
        logger.exception(
            'Unexpected error accepting invitation via API',
            extra={
                'token_prefix': token[:10] + '...',
                'user_id': user_id,
                'error': str(e),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='An unexpected error occurred',
        )