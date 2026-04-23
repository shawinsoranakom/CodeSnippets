async def create_jira_dc_workspace(
    request: Request, workspace_data: JiraDcWorkspaceCreate
):
    """Create a new Jira DC workspace registration."""
    try:
        user_auth = cast(SaasUserAuth, await get_user_auth(request))
        user_id = await user_auth.get_user_id()
        user_email = await user_auth.get_user_email()

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='User ID not found',
            )

        if JIRA_DC_ENABLE_OAUTH:
            # OAuth flow enabled - create session and redirect to OAuth
            state = str(uuid.uuid4())

            integration_session = {
                'operation_type': 'workspace_integration',
                'keycloak_user_id': user_id,
                'user_email': user_email,
                'target_workspace': workspace_data.workspace_name,
                'webhook_secret': workspace_data.webhook_secret,
                'svc_acc_email': workspace_data.svc_acc_email,
                'svc_acc_api_key': workspace_data.svc_acc_api_key,
                'is_active': workspace_data.is_active,
                'state': state,
            }

            created = redis_client.setex(
                state,
                60,
                json.dumps(integration_session),
            )

            if not created:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail='Failed to create integration session',
                )

            auth_params = {
                'client_id': JIRA_DC_CLIENT_ID,
                'scope': JIRA_DC_SCOPES,
                'redirect_uri': JIRA_DC_REDIRECT_URI,
                'state': state,
                'response_type': 'code',
            }

            auth_url = f'{JIRA_DC_AUTH_URL}?{urlencode(auth_params)}'

            return JSONResponse(
                content={
                    'success': True,
                    'redirect': True,
                    'authorizationUrl': auth_url,
                }
            )
        else:
            # OAuth flow disabled - directly create workspace
            workspace = await jira_dc_manager.integration_store.get_workspace_by_name(
                workspace_data.workspace_name
            )
            if not workspace:
                # Create new workspace if it doesn't exist
                encrypted_webhook_secret = token_manager.encrypt_text(
                    workspace_data.webhook_secret
                )
                encrypted_svc_acc_api_key = token_manager.encrypt_text(
                    workspace_data.svc_acc_api_key
                )

                workspace = await jira_dc_manager.integration_store.create_workspace(
                    name=workspace_data.workspace_name,
                    admin_user_id=user_id,
                    encrypted_webhook_secret=encrypted_webhook_secret,
                    svc_acc_email=workspace_data.svc_acc_email,
                    encrypted_svc_acc_api_key=encrypted_svc_acc_api_key,
                    status='active' if workspace_data.is_active else 'inactive',
                )

                # Create a workspace link for the user (admin automatically gets linked)
                await _handle_workspace_link_creation(
                    user_id, 'unavailable', workspace.name
                )
            else:
                # Workspace exists - validate user can update it
                await _validate_workspace_update_permissions(
                    user_id, workspace_data.workspace_name
                )

                encrypted_webhook_secret = token_manager.encrypt_text(
                    workspace_data.webhook_secret
                )
                encrypted_svc_acc_api_key = token_manager.encrypt_text(
                    workspace_data.svc_acc_api_key
                )

                # Update workspace details
                await jira_dc_manager.integration_store.update_workspace(
                    id=workspace.id,
                    encrypted_webhook_secret=encrypted_webhook_secret,
                    svc_acc_email=workspace_data.svc_acc_email,
                    encrypted_svc_acc_api_key=encrypted_svc_acc_api_key,
                    status='active' if workspace_data.is_active else 'inactive',
                )

                await _handle_workspace_link_creation(
                    user_id, 'unavailable', workspace.name
                )
            return JSONResponse(
                content={
                    'success': True,
                    'redirect': False,
                    'authorizationUrl': '',
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f'Error creating Jira DC workspace: {e}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Failed to create workspace',
        )