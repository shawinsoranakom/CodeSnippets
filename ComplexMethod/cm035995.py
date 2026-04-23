async def verify_webhook_conditions(
    gitlab_service: SaaSGitLabService,
    resource_type: GitLabResourceType,
    resource_id: str,
    webhook_store: GitlabWebhookStore,
    webhook: GitlabWebhook,
) -> None:
    """
    Verify all conditions are met for webhook installation.
    Raises BreakLoopException if any condition fails or rate limited.

    Args:
        gitlab_service: GitLab service instance
        resource_type: Type of resource (PROJECT or GROUP)
        resource_id: ID of the resource
        webhook_store: Webhook store instance
        webhook: Webhook object to verify
    """
    # Check if resource exists
    does_resource_exist, status = await gitlab_service.check_resource_exists(
        resource_type, resource_id
    )

    logger.info(
        'Does resource exists',
        extra={
            'does_resource_exist': does_resource_exist,
            'status': status,
            'resource_id': resource_id,
            'resource_type': resource_type,
        },
    )

    if status == WebhookStatus.RATE_LIMITED:
        raise BreakLoopException()
    if not does_resource_exist and status != WebhookStatus.RATE_LIMITED:
        await webhook_store.delete_webhook(webhook)
        raise BreakLoopException()

    # Check if user has admin access
    (
        is_user_admin_of_resource,
        status,
    ) = await gitlab_service.check_user_has_admin_access_to_resource(
        resource_type, resource_id
    )

    logger.info(
        'Is user admin',
        extra={
            'is_user_admin': is_user_admin_of_resource,
            'status': status,
            'resource_id': resource_id,
            'resource_type': resource_type,
        },
    )

    if status == WebhookStatus.RATE_LIMITED:
        raise BreakLoopException()
    if not is_user_admin_of_resource:
        await webhook_store.delete_webhook(webhook)
        raise BreakLoopException()

    # Check if webhook already exists
    (
        does_webhook_exist_on_resource,
        status,
    ) = await gitlab_service.check_webhook_exists_on_resource(
        resource_type=resource_type,
        resource_id=resource_id,
        webhook_url=GITLAB_WEBHOOK_URL,
    )

    logger.info(
        'Does webhook already exist',
        extra={
            'does_webhook_exist_on_resource': does_webhook_exist_on_resource,
            'status': status,
            'resource_id': resource_id,
            'resource_type': resource_type,
        },
    )

    if status == WebhookStatus.RATE_LIMITED:
        raise BreakLoopException()
    if does_webhook_exist_on_resource != webhook.webhook_exists:
        await webhook_store.update_webhook(
            webhook, {'webhook_exists': does_webhook_exist_on_resource}
        )

    if does_webhook_exist_on_resource:
        raise BreakLoopException()