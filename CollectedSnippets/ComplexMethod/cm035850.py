async def jira_callback(request: Request, code: str, state: str):
    integration_session_json = redis_client.get(state)
    if not integration_session_json:
        raise HTTPException(
            status_code=400, detail='No active integration session found.'
        )

    integration_session = json.loads(integration_session_json)

    # Security check: verify the state parameter
    if integration_session.get('state') != state:
        raise HTTPException(
            status_code=400, detail='State mismatch. Possible CSRF attack.'
        )

    token_payload = {
        'grant_type': 'authorization_code',
        'client_id': JIRA_CLIENT_ID,
        'client_secret': JIRA_CLIENT_SECRET,
        'code': code,
        'redirect_uri': JIRA_REDIRECT_URI,
    }
    response = requests.post(JIRA_TOKEN_URL, json=token_payload)
    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail=f'Error fetching token: {response.text}'
        )

    token_data = response.json()
    access_token = token_data['access_token']

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(JIRA_RESOURCES_URL, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=400, detail=f'Error fetching resources: {response.text}'
        )

    workspaces = response.json()

    logger.info(f'Jira workspaces: {workspaces}')

    target_workspace = integration_session.get('target_workspace')

    # Filter workspaces based on the target workspace
    target_workspace_data = next(
        (
            ws
            for ws in workspaces
            if urlparse(ws.get('url', '')).hostname == target_workspace
        ),
        None,
    )
    if not target_workspace_data:
        raise HTTPException(
            status_code=401,
            detail=f'User is not authorized to access workspace: {target_workspace}',
        )

    jira_cloud_id = target_workspace_data.get('id', '')

    jira_user_response = requests.get(JIRA_USER_INFO_URL, headers=headers)
    if jira_user_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f'Error fetching user info: {jira_user_response.text}',
        )

    jira_user_info = jira_user_response.json()
    jira_user_id = jira_user_info.get('account_id')

    user_id = integration_session['keycloak_user_id']

    if integration_session.get('operation_type') == 'workspace_integration':
        workspace = await jira_manager.integration_store.get_workspace_by_name(
            target_workspace
        )
        if not workspace:
            # Create new workspace if it doesn't exist
            encrypted_webhook_secret = token_manager.encrypt_text(
                integration_session['webhook_secret']
            )
            encrypted_svc_acc_api_key = token_manager.encrypt_text(
                integration_session['svc_acc_api_key']
            )

            await jira_manager.integration_store.create_workspace(
                name=target_workspace,
                jira_cloud_id=jira_cloud_id,
                admin_user_id=integration_session['keycloak_user_id'],
                encrypted_webhook_secret=encrypted_webhook_secret,
                svc_acc_email=integration_session['svc_acc_email'],
                encrypted_svc_acc_api_key=encrypted_svc_acc_api_key,
                status='active' if integration_session['is_active'] else 'inactive',
            )

            # Create a workspace link for the user (admin automatically gets linked)
            await _handle_workspace_link_creation(
                user_id, jira_user_id, target_workspace
            )
        else:
            # Workspace exists - validate user can update it
            await _validate_workspace_update_permissions(user_id, target_workspace)

            encrypted_webhook_secret = token_manager.encrypt_text(
                integration_session['webhook_secret']
            )
            encrypted_svc_acc_api_key = token_manager.encrypt_text(
                integration_session['svc_acc_api_key']
            )

            # Update workspace details
            await jira_manager.integration_store.update_workspace(
                id=workspace.id,
                jira_cloud_id=jira_cloud_id,
                encrypted_webhook_secret=encrypted_webhook_secret,
                svc_acc_email=integration_session['svc_acc_email'],
                encrypted_svc_acc_api_key=encrypted_svc_acc_api_key,
                status='active' if integration_session['is_active'] else 'inactive',
            )

            await _handle_workspace_link_creation(
                user_id, jira_user_id, target_workspace
            )

        return RedirectResponse(
            url='/settings/integrations', status_code=status.HTTP_302_FOUND
        )
    elif integration_session.get('operation_type') == 'workspace_link':
        await _handle_workspace_link_creation(user_id, jira_user_id, target_workspace)
        return RedirectResponse(
            url='/settings/integrations', status_code=status.HTTP_302_FOUND
        )
    else:
        raise HTTPException(status_code=400, detail='Invalid operation type')