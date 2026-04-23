async def _build_start_conversation_request_for_user(
        self,
        sandbox: SandboxInfo,
        conversation_id: UUID,
        initial_message: SendMessageRequest | None,
        system_message_suffix: str | None,
        git_provider: ProviderType | None,
        working_dir: str,
        agent_type: AgentType = AgentType.DEFAULT,
        llm_model: str | None = None,
        remote_workspace: AsyncRemoteWorkspace | None = None,
        selected_repository: str | None = None,
        plugins: list[PluginSpec] | None = None,
    ) -> StartConversationRequest:
        """Build a complete StartConversationRequest for a user.

        Resolves LLM, MCP, tools, secrets and agent context, then
        builds the ``Agent`` via ``AgentSettings.create_agent()``.
        Server-only overrides (system prompts, LLM tracing metadata,
        skills, hooks) are applied to the agent after creation.
        Finally delegates to ``ConversationSettings.create_request()``.
        """
        user = await self.user_context.get_user_info()

        project_dir = get_project_dir(working_dir, selected_repository)
        workspace = LocalWorkspace(working_dir=project_dir)

        # --- secrets --------------------------------------------------------
        secrets = await self._setup_secrets_for_git_providers(user)

        # --- LLM + MCP -----------------------------------------------------
        llm, mcp_config = await self._configure_llm_and_mcp(
            user, llm_model, conversation_id
        )

        # --- system_message_suffix (planning-agent prefix) ------------------
        effective_suffix = system_message_suffix
        if agent_type == AgentType.PLAN:
            if system_message_suffix:
                effective_suffix = (
                    f'{PLANNING_AGENT_INSTRUCTION}\n\n{system_message_suffix}'
                )
            else:
                effective_suffix = PLANNING_AGENT_INSTRUCTION

        # --- web host context -----------------------------------------------
        # Add WEB_HOST to agent context if available
        if self.web_url:
            web_host_context = f'<HOST>\n{self.web_url}\n</HOST>'
            if effective_suffix:
                effective_suffix = f'{effective_suffix}\n\n{web_host_context}'
            else:
                effective_suffix = web_host_context

        # --- tools ----------------------------------------------------------
        if agent_type == AgentType.PLAN:
            plan_path = None
            if project_dir:
                plan_path = self._compute_plan_path(project_dir, git_provider)
            tools = get_planning_tools(plan_path=plan_path)
        else:
            tools = get_default_tools(enable_browser=True)

        # --- build AgentSettings and create agent ---------------------------
        from fastmcp.mcp_config import MCPConfig

        configured_agent_settings = user.agent_settings.model_copy(
            update={
                'llm': llm,
                'tools': tools,
                'mcp_config': MCPConfig(**mcp_config) if mcp_config else None,
                'agent_context': AgentContext(
                    system_message_suffix=effective_suffix,
                    secrets=secrets,
                ),
            }
        )
        agent = configured_agent_settings.create_agent()
        agent = self._apply_server_agent_overrides(
            agent, agent_type, mcp_config, conversation_id, user.id
        )

        # --- skills + hooks (require remote workspace) ----------------------
        hook_config: HookConfig | None = None
        if remote_workspace:
            try:
                agent = await self._load_skills_and_update_agent(
                    sandbox,
                    agent,
                    remote_workspace,
                    selected_repository,
                    project_dir,
                    disabled_skills=user.disabled_skills,
                )
            except Exception as e:
                _logger.warning(f'Failed to load skills: {e}', exc_info=True)

            try:
                _logger.debug(
                    f'Attempting to load hooks from workspace: '
                    f'project_dir={project_dir}'
                )
                hook_config = await self._load_hooks_from_workspace(
                    remote_workspace, project_dir
                )
                if hook_config:
                    _logger.debug(
                        f'Successfully loaded hooks: {hook_config.model_dump()}'
                    )
                else:
                    _logger.debug('No hooks found in workspace')
            except Exception as e:
                _logger.warning(f'Failed to load hooks: {e}', exc_info=True)

        # --- plugins --------------------------------------------------------
        final_initial_message = self._construct_initial_message_with_plugin_params(
            initial_message, plugins
        )
        sdk_plugins: list[PluginSource] | None = None
        if plugins:
            sdk_plugins = [
                PluginSource(
                    source=p.source,
                    ref=p.ref,
                    repo_path=p.repo_path,
                )
                for p in plugins
            ]

        # --- populate ConversationSettings and build request ----------------
        conv_settings = user.conversation_settings.model_copy(
            update={
                'agent_settings': configured_agent_settings,
                'workspace': workspace,
                'conversation_id': conversation_id,
                'initial_message': final_initial_message,
                'plugins': sdk_plugins,
                'hook_config': hook_config,
            }
        )

        # Pass agent explicitly — it has server-only overrides (system
        # prompts, LLM metadata, skills) applied after create_agent().
        return conv_settings.create_request(StartConversationRequest, agent=agent)