async def run_auto_gpt(
    continuous: bool = False,
    continuous_limit: Optional[int] = None,
    skip_reprompt: bool = False,
    speak: bool = False,
    debug: bool = False,
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file_format: Optional[str] = None,
    skip_news: bool = False,
    install_plugin_deps: bool = False,
    override_ai_name: Optional[str] = None,
    override_ai_role: Optional[str] = None,
    resources: Optional[list[str]] = None,
    constraints: Optional[list[str]] = None,
    best_practices: Optional[list[str]] = None,
    override_directives: bool = False,
    component_config_file: Optional[Path] = None,
    workspace: Optional[Path] = None,
):
    # Determine workspace directory - default to current working directory
    if workspace is None:
        workspace = Path.cwd()

    # Set up configuration
    config = ConfigBuilder.build_config_from_env(workspace=workspace)

    # Agent data is stored in .autogpt/ subdirectory of the workspace
    data_dir = workspace / ".autogpt"

    # Load workspace settings (creates autogpt.yaml if missing)
    workspace_settings = WorkspaceSettings.load_or_create(workspace)

    # Storage
    # For CLI mode, root file storage at the workspace root (cwd) so agents can access
    # project files directly. Agent state is still stored in .autogpt/agents/{id}/.
    local = config.file_storage_backend == FileStorageBackendName.LOCAL
    restrict_to_root = not local or config.restrict_to_workspace
    file_storage = get_storage(
        config.file_storage_backend,
        root_path=workspace,
        restrict_to_root=restrict_to_root,
    )
    file_storage.initialize()

    # Create prompt callback for permission requests
    def prompt_permission(
        cmd: str, args_str: str, args: dict
    ) -> tuple[ApprovalScope, str | None]:
        """Prompt user for command permission.

        Uses an interactive selector with arrow keys and a feedback option.

        Args:
            cmd: Command name.
            args_str: Formatted arguments string.
            args: Full arguments dictionary.

        Returns:
            Tuple of (ApprovalScope, feedback). Feedback is None if not provided.
        """
        from autogpt.app.ui.rich_select import RichSelect

        choices = [
            "Once",
            "Always (this agent)",
            "Always (all agents)",
            "Deny",
        ]

        scope_map = {
            0: ApprovalScope.ONCE,
            1: ApprovalScope.AGENT,
            2: ApprovalScope.WORKSPACE,
            3: ApprovalScope.DENY,
        }

        selector = RichSelect(
            choices=choices,
            title="Approve command execution?",
            subtitle=f"{cmd}({args_str})",
        )
        result = selector.run()

        scope = scope_map.get(result.index, ApprovalScope.DENY)
        feedback = result.feedback if result.has_feedback else None
        return (scope, feedback)

    def display_auto_approved(
        cmd: str, args_str: str, args: dict, scope: ApprovalScope
    ) -> None:
        """Display auto-approved command execution using Rich.

        Called when a command is auto-approved from the allow lists,
        so the user can see what's executing without needing to approve.

        Args:
            cmd: Command name.
            args_str: Formatted arguments string.
            args: Full arguments dictionary.
            scope: The scope that granted the auto-approval.
        """
        from rich.console import Console
        from rich.text import Text

        console = Console()

        # Build the display text
        scope_label = "agent" if scope == ApprovalScope.AGENT else "workspace"
        text = Text()
        text.append("  ✓ ", style="bold green")
        text.append("Auto-approved ", style="dim")
        text.append(f"({scope_label})", style="dim cyan")
        text.append(": ", style="dim")
        text.append(cmd, style="bold cyan")
        text.append("(", style="dim")
        # Truncate args if too long
        display_args = args_str[:60] + "..." if len(args_str) > 60 else args_str
        text.append(display_args, style="dim")
        text.append(")", style="dim")

        console.print(text)

    # Set up logging module
    if speak:
        config.tts_config.speak_mode = True
    configure_logging(
        debug=debug,
        level=log_level,
        log_format=log_format,
        log_file_format=log_file_format,
        config=config.logging,
        tts_config=config.tts_config,
    )

    await assert_config_has_required_llm_api_keys(config)

    await apply_overrides_to_config(
        config=config,
        continuous=continuous,
        continuous_limit=continuous_limit,
        skip_reprompt=skip_reprompt,
        skip_news=skip_news,
    )

    llm_provider = _configure_llm_provider(config)

    logger = logging.getLogger(__name__)

    if config.continuous_mode:
        for line in get_legal_warning().split("\n"):
            logger.warning(
                extra={
                    "title": "LEGAL:",
                    "title_color": Fore.RED,
                    "preserve_color": True,
                },
                msg=markdown_to_ansi_style(line),
            )

    if not config.skip_news:
        print_motd(logger)
        print_git_branch_info(logger)
        print_python_version_info(logger)
        print_attribute("Smart LLM", config.smart_llm)
        print_attribute("Fast LLM", config.fast_llm)
        if config.continuous_mode:
            print_attribute("Continuous Mode", "ENABLED", title_color=Fore.YELLOW)
            if continuous_limit:
                print_attribute("Continuous Limit", config.continuous_limit)
        if config.tts_config.speak_mode:
            print_attribute("Speak Mode", "ENABLED")
        if we_are_running_in_a_docker_container() or is_docker_available():
            print_attribute("Code Execution", "ENABLED")
        else:
            print_attribute(
                "Code Execution",
                "DISABLED (Docker unavailable)",
                title_color=Fore.YELLOW,
            )

    # Let user choose an existing agent to run
    # For CLI mode, AgentManager needs to look in .autogpt/agents/, not agents/
    # Since file_storage is rooted at workspace, we need to clone with .autogpt subroot
    agent_storage = file_storage.clone_with_subroot(".autogpt")
    agent_manager = AgentManager(agent_storage)
    existing_agents = agent_manager.list_agents()
    load_existing_agent = ""
    if existing_agents:
        print(
            "Existing agents\n---------------\n"
            + "\n".join(f"{i} - {id}" for i, id in enumerate(existing_agents, 1))
        )
        load_existing_agent = clean_input(
            "Enter the number or name of the agent to run,"
            " or hit enter to create a new one:",
        )
        if re.match(r"^\d+$", load_existing_agent.strip()) and 0 < int(
            load_existing_agent
        ) <= len(existing_agents):
            load_existing_agent = existing_agents[int(load_existing_agent) - 1]

        if load_existing_agent != "" and load_existing_agent not in existing_agents:
            logger.info(
                f"Unknown agent '{load_existing_agent}', "
                f"creating a new one instead.",
                extra={"color": Fore.YELLOW},
            )
            load_existing_agent = ""

    # Either load existing or set up new agent state
    agent = None
    agent_state = None

    ############################
    # Resume an Existing Agent #
    ############################
    if load_existing_agent:
        agent_state = None
        while True:
            answer = clean_input("Resume? [Y/n]")
            if answer == "" or answer.lower() == "y":
                agent_state = agent_manager.load_agent_state(load_existing_agent)
                break
            elif answer.lower() == "n":
                break

    if agent_state:
        # Create permission manager for this agent
        agent_dir = data_dir / "agents" / agent_state.agent_id
        agent_permissions = AgentPermissions.load_or_create(agent_dir)
        perm_manager = CommandPermissionManager(
            workspace=workspace,
            agent_dir=agent_dir,
            workspace_settings=workspace_settings,
            agent_permissions=agent_permissions,
            prompt_fn=prompt_permission if not config.noninteractive_mode else None,
            on_auto_approve=(
                display_auto_approved if not config.noninteractive_mode else None
            ),
        )

        agent = configure_agent_with_state(
            state=agent_state,
            app_config=config,
            file_storage=file_storage,
            llm_provider=llm_provider,
            permission_manager=perm_manager,
        )
        apply_overrides_to_ai_settings(
            ai_profile=agent.state.ai_profile,
            directives=agent.state.directives,
            override_name=override_ai_name,
            override_role=override_ai_role,
            resources=resources,
            constraints=constraints,
            best_practices=best_practices,
            replace_directives=override_directives,
        )

        if (
            (current_episode := agent.event_history.current_episode)
            and current_episode.action.use_tool.name == FINISH_COMMAND
            and not current_episode.result
        ):
            # Agent was resumed after `finish` -> rewrite result of `finish` action
            finish_reason = current_episode.action.use_tool.arguments["reason"]
            print(f"Agent previously self-terminated; reason: '{finish_reason}'")
            new_assignment = clean_input(
                "Please give a follow-up question or assignment:"
            )
            agent.event_history.register_result(
                ActionInterruptedByHuman(feedback=new_assignment)
            )

        # If any of these are specified as arguments,
        #  assume the user doesn't want to revise them
        if not any(
            [
                override_ai_name,
                override_ai_role,
                resources,
                constraints,
                best_practices,
            ]
        ):
            ai_profile, ai_directives = await interactively_revise_ai_settings(
                ai_profile=agent.state.ai_profile,
                directives=agent.state.directives,
                app_config=config,
            )
        else:
            logger.info("AI config overrides specified through CLI; skipping revision")

    ######################
    # Set up a new Agent #
    ######################
    if not agent:
        task = ""
        while task.strip() == "":
            task = clean_input(
                "Enter the task that you want AutoGPT to execute,"
                " with as much detail as possible:",
            )

        ai_profile = AIProfile()
        additional_ai_directives = AIDirectives()
        apply_overrides_to_ai_settings(
            ai_profile=ai_profile,
            directives=additional_ai_directives,
            override_name=override_ai_name,
            override_role=override_ai_role,
            resources=resources,
            constraints=constraints,
            best_practices=best_practices,
            replace_directives=override_directives,
        )

        # If any of these are specified as arguments,
        #  assume the user doesn't want to revise them
        if not any(
            [
                override_ai_name,
                override_ai_role,
                resources,
                constraints,
                best_practices,
            ]
        ):
            (
                ai_profile,
                additional_ai_directives,
            ) = await interactively_revise_ai_settings(
                ai_profile=ai_profile,
                directives=additional_ai_directives,
                app_config=config,
            )
        else:
            logger.info("AI config overrides specified through CLI; skipping revision")

        # Generate agent ID and create permission manager
        new_agent_id = agent_manager.generate_id(ai_profile.ai_name)
        agent_dir = data_dir / "agents" / new_agent_id
        agent_permissions = AgentPermissions.load_or_create(agent_dir)
        perm_manager = CommandPermissionManager(
            workspace=workspace,
            agent_dir=agent_dir,
            workspace_settings=workspace_settings,
            agent_permissions=agent_permissions,
            prompt_fn=prompt_permission if not config.noninteractive_mode else None,
            on_auto_approve=(
                display_auto_approved if not config.noninteractive_mode else None
            ),
        )

        agent = create_agent(
            agent_id=new_agent_id,
            task=task,
            ai_profile=ai_profile,
            directives=additional_ai_directives,
            app_config=config,
            file_storage=file_storage,
            llm_provider=llm_provider,
            permission_manager=perm_manager,
        )

        file_manager = agent.file_manager

        if file_manager and not agent.config.allow_fs_access:
            logger.info(
                f"{Fore.YELLOW}"
                "NOTE: All files/directories created by this agent can be found "
                f"inside its workspace at:{Fore.RESET} {file_manager.workspace.root}",
                extra={"preserve_color": True},
            )

        # TODO: re-evaluate performance benefit of task-oriented profiles
        # # Concurrently generate a custom profile for the agent and apply it once done
        # def update_agent_directives(
        #     task: asyncio.Task[tuple[AIProfile, AIDirectives]]
        # ):
        #     logger.debug(f"Updating AIProfile: {task.result()[0]}")
        #     logger.debug(f"Adding AIDirectives: {task.result()[1]}")
        #     agent.state.ai_profile = task.result()[0]
        #     agent.state.directives = agent.state.directives + task.result()[1]

        # asyncio.create_task(
        #     generate_agent_profile_for_task(
        #         task, app_config=config, llm_provider=llm_provider
        #     )
        # ).add_done_callback(update_agent_directives)

    # Load component configuration from file
    if _config_file := component_config_file or config.component_config_file:
        try:
            logger.info(f"Loading component configuration from {_config_file}")
            agent.load_component_configs(_config_file.read_text())
        except Exception as e:
            logger.error(f"Could not load component configuration: {e}")

    #################
    # Run the Agent #
    #################
    # Create UI provider for terminal output
    ui_provider = create_ui_provider(
        plain_output=config.logging.plain_console_output,
    )

    async def handle_agent_termination():
        """Handle agent termination by saving state."""
        agent_id = agent.state.agent_id
        logger.info(f"Saving state of {agent_id}...")

        # Allow user to Save As other ID
        save_as_id = clean_input(
            f"Press enter to save as '{agent_id}',"
            " or enter a different ID to save to:",
        )
        # TODO: allow many-to-one relations of agents and workspaces
        await agent.file_manager.save_state(
            save_as_id.strip() if not save_as_id.isspace() else None
        )

    try:
        await run_interaction_loop(agent, ui_provider)
    except AgentTerminated:
        await handle_agent_termination()