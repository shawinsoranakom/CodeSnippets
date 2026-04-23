async def update_project_mcp_settings(
    project_id: UUID,
    request: MCPProjectUpdateRequest,
    current_user: CurrentActiveMCPUser,
):
    """Update the MCP settings of all flows in a project and project-level auth settings.

    On MCP Composer failure, this endpoint should return with a 200 status code and an error message in
    the body of the response to display to the user.
    """
    try:
        async with session_scope() as session:
            # Fetch the project first to verify it exists and belongs to the current user
            project = (
                await session.exec(
                    select(Folder)
                    .options(selectinload(Folder.flows))
                    .where(Folder.id == project_id, Folder.user_id == current_user.id)
                )
            ).first()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Track if MCP Composer needs to be started or stopped
            should_handle_mcp_composer = False
            should_start_composer = False
            should_stop_composer = False

            # Store original auth settings in case we need to rollback
            original_auth_settings = project.auth_settings

            # Update project-level auth settings with encryption
            if "auth_settings" in request.model_fields_set and request.auth_settings is not None:
                auth_result = handle_auth_settings_update(
                    existing_project=project,
                    new_auth_settings=request.auth_settings,
                )

                should_handle_mcp_composer = auth_result["should_handle_composer"]
                should_start_composer = auth_result["should_start_composer"]
                should_stop_composer = auth_result["should_stop_composer"]

            # Query flows in the project
            flows = (await session.exec(select(Flow).where(Flow.folder_id == project_id))).all()
            flows_to_update = {x.id: x for x in request.settings}

            updated_flows = []
            for flow in flows:
                if flow.user_id is None or flow.user_id != current_user.id:
                    continue

                if flow.id in flows_to_update:
                    settings_to_update = flows_to_update[flow.id]
                    flow.mcp_enabled = settings_to_update.mcp_enabled
                    flow.action_name = settings_to_update.action_name
                    flow.action_description = settings_to_update.action_description
                    flow.updated_at = datetime.now(timezone.utc)
                    session.add(flow)
                    updated_flows.append(flow)

            await session.flush()

            response: dict[str, Any] = {
                "message": f"Updated MCP settings for {len(updated_flows)} flows and project auth settings"
            }

            # Handle MCP Composer start/stop before committing auth settings
            if should_handle_mcp_composer:
                # Get MCP Composer service once for all branches
                mcp_composer_service: MCPComposerService = cast(
                    MCPComposerService, get_service(ServiceType.MCP_COMPOSER_SERVICE)
                )

                if should_start_composer:
                    await logger.adebug(
                        f"Auth settings changed to OAuth for project {project.name} ({project_id}), "
                        "starting MCP Composer"
                    )

                    if should_use_mcp_composer(project):
                        try:
                            auth_config = await _get_mcp_composer_auth_config(project)
                            await get_or_start_mcp_composer(auth_config, project.name, project_id)
                            composer_streamable_http_url = await get_composer_streamable_http_url(project)
                            composer_sse_url = await get_composer_sse_url(project)
                            # Clear any previous error on success
                            mcp_composer_service.clear_last_error(str(project_id))
                            response["result"] = {
                                "project_id": str(project_id),
                                "streamable_http_url": composer_streamable_http_url,
                                "legacy_sse_url": composer_sse_url,
                                "sse_url": composer_sse_url,
                                "uses_composer": True,
                            }
                        except MCPComposerError as e:
                            # Don't rollback auth settings - persist them so UI can show the error
                            await logger.awarning(f"MCP Composer failed to start for project {project_id}: {e.message}")
                            # Store the error message so it can be retrieved via composer-url endpoint
                            mcp_composer_service.set_last_error(str(project_id), e.message)
                            response["result"] = {
                                "project_id": str(project_id),
                                "uses_composer": True,
                                "error_message": e.message,
                            }
                        except Exception as e:
                            # Rollback auth settings on unexpected errors
                            await logger.aerror(
                                f"Unexpected error starting MCP Composer for project {project_id}, "
                                f"rolling back auth settings: {e}"
                            )
                            project.auth_settings = original_auth_settings
                            raise HTTPException(status_code=500, detail=str(e)) from e
                    else:
                        # OAuth is set but MCP Composer is disabled - save settings but return error
                        # Don't rollback - keep the auth settings so they can be used when composer is enabled
                        await logger.aerror(
                            f"PATCH: OAuth set but MCP Composer is disabled in settings for project {project_id}"
                        )
                        response["result"] = {
                            "project_id": str(project_id),
                            "uses_composer": False,
                            "error_message": "OAuth authentication is set but MCP Composer is disabled in settings",
                        }
                elif should_stop_composer:
                    await logger.adebug(
                        f"Auth settings changed from OAuth for project {project.name} ({project_id}), "
                        "stopping MCP Composer"
                    )
                    await mcp_composer_service.stop_project_composer(str(project_id))
                    # Clear any error when user explicitly disables OAuth
                    mcp_composer_service.clear_last_error(str(project_id))

                    # Provide direct connection URLs since we're no longer using composer
                    streamable_http_url = await get_project_streamable_http_url(project_id)
                    legacy_sse_url = await get_project_sse_url(project_id)
                    if not streamable_http_url:
                        raise HTTPException(status_code=500, detail="Failed to get direct Streamable HTTP URL")

                    response["result"] = {
                        "project_id": str(project_id),
                        "streamable_http_url": streamable_http_url,
                        "legacy_sse_url": legacy_sse_url,
                        "sse_url": legacy_sse_url,
                        "uses_composer": False,
                    }

            # Only commit if composer started successfully (or wasn't needed)
            session.add(project)
            await session.commit()

            return response

    except Exception as e:
        msg = f"Error updating project MCP settings: {e!s}"
        await logger.aexception(msg)
        raise HTTPException(status_code=500, detail=str(e)) from e