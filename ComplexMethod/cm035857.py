async def reinstall_gitlab_webhook(
    body: ReinstallWebhookRequest,
    user_id: str = Depends(get_user_id),
) -> ResourceInstallationResult:
    """Reinstall GitLab webhook for a specific resource immediately.

    This endpoint validates permissions, resets webhook status in the database,
    and immediately installs the webhook on the specified resource.
    """
    try:
        # Get GitLab service for the user
        gitlab_service = GitLabServiceImpl(external_auth_id=user_id)

        if not isinstance(gitlab_service, SaaSGitLabService):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Only SaaS GitLab service is supported',
            )

        resource_id = body.resource.id
        resource_type = body.resource.type

        # Check if user has admin access to this resource
        (
            has_admin_access,
            check_status,
        ) = await gitlab_service.check_user_has_admin_access_to_resource(
            resource_type, resource_id
        )

        if not has_admin_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='User does not have admin access to this resource',
            )

        # Reset webhook in database (organization-wide, not user-specific)
        # This allows any admin user to reinstall webhooks
        await webhook_store.reset_webhook_for_reinstallation_by_resource(
            resource_type, resource_id, user_id
        )

        # Get or create webhook record (without user_id filter)
        webhook = await webhook_store.get_webhook_by_resource_only(
            resource_type, resource_id
        )

        if not webhook:
            # Create new webhook record
            webhook = GitlabWebhook(
                user_id=user_id,  # Track who created it
                project_id=resource_id
                if resource_type == GitLabResourceType.PROJECT
                else None,
                group_id=resource_id
                if resource_type == GitLabResourceType.GROUP
                else None,
                webhook_exists=False,
            )
            await webhook_store.store_webhooks([webhook])
            # Fetch it again to get the ID (without user_id filter)
            webhook = await webhook_store.get_webhook_by_resource_only(
                resource_type, resource_id
            )

        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to create or fetch webhook record',
            )

        # Verify conditions and install webhook
        try:
            await verify_webhook_conditions(
                gitlab_service=gitlab_service,
                resource_type=resource_type,
                resource_id=resource_id,
                webhook_store=webhook_store,
                webhook=webhook,
            )

            # Install the webhook
            webhook_id, install_status = await install_webhook_on_resource(
                gitlab_service=gitlab_service,
                resource_type=resource_type,
                resource_id=resource_id,
                webhook_store=webhook_store,
                webhook=webhook,
            )

            if webhook_id:
                logger.info(
                    'GitLab webhook reinstalled successfully',
                    extra={
                        'user_id': user_id,
                        'resource_type': resource_type.value,
                        'resource_id': resource_id,
                    },
                )
                return ResourceInstallationResult(
                    resource_id=resource_id,
                    resource_type=resource_type.value,
                    success=True,
                    error=None,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail='Failed to install webhook',
                )

        except BreakLoopException:
            # Conditions not met or webhook already exists
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Webhook installation conditions not met or webhook already exists',
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Error reinstalling GitLab webhook: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to reinstall webhook',
        )