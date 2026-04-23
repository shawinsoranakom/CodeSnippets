async def _start_app_conversation(
        self, request: AppConversationStartRequest
    ) -> AsyncGenerator[AppConversationStartTask, None]:
        # Create and yield the start task
        user_id = await self.user_context.get_user_id()

        # Validate and inherit from parent conversation if provided
        if request.parent_conversation_id:
            parent_info = (
                await self.app_conversation_info_service.get_app_conversation_info(
                    request.parent_conversation_id
                )
            )
            if parent_info is None:
                raise ValueError(
                    f'Parent conversation not found: {request.parent_conversation_id}'
                )
            self._inherit_configuration_from_parent(request, parent_info)

        self._apply_suggested_task(request)

        task = AppConversationStartTask(
            created_by_user_id=user_id,
            request=request,
        )
        yield task

        try:
            async for updated_task in self._wait_for_sandbox_start(task):
                yield updated_task

            # Get the sandbox
            sandbox_id = task.sandbox_id
            assert sandbox_id is not None
            sandbox = await self.sandbox_service.get_sandbox(sandbox_id)
            assert sandbox is not None
            agent_server_url = self._get_agent_server_url(sandbox)

            # Get the working dir
            sandbox_spec = await self.sandbox_spec_service.get_sandbox_spec(
                sandbox.sandbox_spec_id
            )
            assert sandbox_spec is not None

            # Set up conversation id
            conversation_id = request.conversation_id or uuid4()

            # Setup working dir based on grouping
            working_dir = sandbox_spec.working_dir
            sandbox_grouping_strategy = await self._get_sandbox_grouping_strategy()
            if sandbox_grouping_strategy != SandboxGroupingStrategy.NO_GROUPING:
                working_dir = f'{working_dir}/{conversation_id.hex}'

            # Run setup scripts
            remote_workspace = AsyncRemoteWorkspace(
                host=agent_server_url,
                api_key=sandbox.session_api_key,
                working_dir=working_dir,
            )
            async for updated_task in self.run_setup_scripts(
                task, sandbox, remote_workspace, agent_server_url
            ):
                yield updated_task

            # Build the start request
            start_conversation_request = (
                await self._build_start_conversation_request_for_user(
                    sandbox,
                    conversation_id,
                    request.initial_message,
                    request.system_message_suffix,
                    request.git_provider,
                    working_dir,
                    request.agent_type,
                    request.llm_model,
                    remote_workspace=remote_workspace,
                    selected_repository=request.selected_repository,
                    plugins=request.plugins,
                )
            )

            # update status
            task.status = AppConversationStartTaskStatus.STARTING_CONVERSATION
            task.agent_server_url = agent_server_url
            yield task

            # Start conversation...
            body_json = start_conversation_request.model_dump(
                mode='json', context={'expose_secrets': True}
            )
            # Log hook_config to verify it's being passed
            hook_config_in_request = body_json.get('hook_config')
            _logger.debug(
                f'Sending StartConversationRequest with hook_config: '
                f'{hook_config_in_request}'
            )
            headers = (
                {'X-Session-API-Key': sandbox.session_api_key}
                if sandbox.session_api_key
                else {}
            )
            response = await self.httpx_client.post(
                f'{agent_server_url}/api/conversations',
                json=body_json,
                headers=headers,
                timeout=self.sandbox_startup_timeout,
            )

            response.raise_for_status()
            info = ConversationInfo.model_validate(response.json())

            # Store info...
            user_id = await self.user_context.get_user_id()
            app_conversation_info = AppConversationInfo(
                id=info.id,
                title=f'Conversation {info.id.hex[:5]}',
                sandbox_id=sandbox.id,
                created_by_user_id=user_id,
                llm_model=start_conversation_request.agent.llm.model,
                # Git parameters
                selected_repository=request.selected_repository,
                selected_branch=request.selected_branch,
                git_provider=request.git_provider,
                trigger=request.trigger,
                pr_number=request.pr_number,
                parent_conversation_id=request.parent_conversation_id,
            )
            await self.app_conversation_info_service.save_app_conversation_info(
                app_conversation_info
            )

            # Setup default processors
            processors = request.processors or []

            # Always ensure SetTitleCallbackProcessor is included
            has_set_title_processor = any(
                isinstance(processor, SetTitleCallbackProcessor)
                for processor in processors
            )
            if not has_set_title_processor:
                processors.append(SetTitleCallbackProcessor())

            # Save processors
            for processor in processors:
                await self.event_callback_service.save_event_callback(
                    EventCallback(
                        conversation_id=info.id,
                        processor=processor,
                    )
                )

            # Update the start task
            task.status = AppConversationStartTaskStatus.READY
            task.app_conversation_id = info.id
            yield task

            # Process any pending messages queued while waiting for conversation
            if sandbox.session_api_key:
                await self._process_pending_messages(
                    task_id=task.id,
                    conversation_id=info.id,
                    agent_server_url=agent_server_url,
                    session_api_key=sandbox.session_api_key,
                )

        except Exception as exc:
            _logger.exception('Error starting conversation', stack_info=True)
            task.status = AppConversationStartTaskStatus.ERROR
            task.detail = str(exc)
            yield task