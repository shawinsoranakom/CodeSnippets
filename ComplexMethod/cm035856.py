async def get_gitlab_resources(
    user_id: str = Depends(get_user_id),
) -> GitLabResourcesResponse:
    """Get all GitLab projects and groups where the user has admin access.

    Returns a list of resources with their webhook installation status.
    """
    try:
        # Get GitLab service for the user
        gitlab_service = GitLabServiceImpl(external_auth_id=user_id)

        if not isinstance(gitlab_service, SaaSGitLabService):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Only SaaS GitLab service is supported',
            )

        # Fetch projects and groups with admin access
        projects, groups = await gitlab_service.get_user_resources_with_admin_access()

        # Filter out projects that belong to a group (nested projects)
        # We only want top-level personal projects since group webhooks cover nested projects
        filtered_projects = [
            project
            for project in projects
            if project.get('namespace', {}).get('kind') != 'group'
        ]

        # Extract IDs for bulk fetching
        project_ids = [str(project['id']) for project in filtered_projects]
        group_ids = [str(group['id']) for group in groups]

        # Bulk fetch webhook records from database (organization-wide)
        (
            project_webhook_map,
            group_webhook_map,
        ) = await webhook_store.get_webhooks_by_resources(project_ids, group_ids)

        # Parallelize GitLab API calls to check webhook status for all resources
        async def check_project_webhook(project):
            project_id = str(project['id'])
            webhook_exists, _ = await gitlab_service.check_webhook_exists_on_resource(
                GitLabResourceType.PROJECT, project_id, GITLAB_WEBHOOK_URL
            )
            return project_id, webhook_exists

        async def check_group_webhook(group):
            group_id = str(group['id'])
            webhook_exists, _ = await gitlab_service.check_webhook_exists_on_resource(
                GitLabResourceType.GROUP, group_id, GITLAB_WEBHOOK_URL
            )
            return group_id, webhook_exists

        # Gather all API calls in parallel
        project_checks = [
            check_project_webhook(project) for project in filtered_projects
        ]
        group_checks = [check_group_webhook(group) for group in groups]

        # Execute all checks concurrently
        all_results = await asyncio.gather(*(project_checks + group_checks))

        # Split results back into projects and groups
        num_projects = len(filtered_projects)
        project_results = all_results[:num_projects]
        group_results = all_results[num_projects:]

        # Build response
        resources = []

        # Add projects with their webhook status
        for project, (project_id, webhook_exists) in zip(
            filtered_projects, project_results
        ):
            webhook = project_webhook_map.get(project_id)

            resources.append(
                ResourceWithWebhookStatus(
                    id=project_id,
                    name=project.get('name', ''),
                    full_path=project.get('path_with_namespace', ''),
                    type='project',
                    webhook_installed=webhook_exists,
                    webhook_uuid=webhook.webhook_uuid if webhook else None,
                    last_synced=(
                        webhook.last_synced.isoformat()
                        if webhook and webhook.last_synced
                        else None
                    ),
                )
            )

        # Add groups with their webhook status
        for group, (group_id, webhook_exists) in zip(groups, group_results):
            webhook = group_webhook_map.get(group_id)

            resources.append(
                ResourceWithWebhookStatus(
                    id=group_id,
                    name=group.get('name', ''),
                    full_path=group.get('full_path', ''),
                    type='group',
                    webhook_installed=webhook_exists,
                    webhook_uuid=webhook.webhook_uuid if webhook else None,
                    last_synced=(
                        webhook.last_synced.isoformat()
                        if webhook and webhook.last_synced
                        else None
                    ),
                )
            )

        logger.info(
            'Retrieved GitLab resources',
            extra={
                'user_id': user_id,
                'project_count': len(projects),
                'group_count': len(groups),
            },
        )

        return GitLabResourcesResponse(resources=resources)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Error retrieving GitLab resources: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to retrieve GitLab resources',
        )