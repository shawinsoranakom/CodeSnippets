async def update_org_member(
    org_id: UUID,
    user_id: str,
    update_data: OrgMemberUpdate,
    current_user_id: str = Depends(get_user_id),
) -> OrgMemberResponse:
    """Update a member's role in an organization.

    Permission rules:
    - Admins can change roles of regular members to Admin or Member
    - Admins cannot modify other Admins or Owners
    - Owners can change roles of Admins and Members to any role (Owner, Admin, Member)
    - Owners cannot modify other Owners

    Members cannot modify their own role. The last owner cannot be demoted.
    """
    try:
        return await OrgMemberService.update_org_member(
            org_id=org_id,
            target_user_id=UUID(user_id),
            current_user_id=UUID(current_user_id),
            update_data=update_data,
        )
    except OrgMemberNotFoundError as e:
        # Distinguish between requester not being a member vs target not found
        if str(current_user_id) in str(e):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='You are not a member of this organization',
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Member not found in this organization',
        )
    except CannotModifySelfError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Cannot modify your own role',
        )
    except RoleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Role configuration error',
        )
    except InvalidRoleError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid role specified',
        )
    except InsufficientPermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You do not have permission to modify this member',
        )
    except LastOwnerError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Cannot demote the last owner of an organization',
        )
    except MemberUpdateError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update member',
        )
    except ValueError:
        logger.exception('Invalid UUID format')
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid organization or user ID format',
        )
    except Exception:
        logger.exception('Error updating organization member')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to update member',
        )