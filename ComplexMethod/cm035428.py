def __init__(
        self,
        config: OpenHandsConfig,
        event_stream: EventStream,
        llm_registry: LLMRegistry,
        sid: str = 'default',
        plugins: list[PluginRequirement] | None = None,
        env_vars: dict[str, str] | None = None,
        status_callback: Callable[[str, RuntimeStatus, str], None] | None = None,
        attach_to_existing: bool = False,
        headless_mode: bool = False,
        user_id: str | None = None,
        git_provider_tokens: PROVIDER_TOKEN_TYPE | None = None,
    ):
        self.git_handler = GitHandler(
            execute_shell_fn=self._execute_shell_fn_git_handler,
            create_file_fn=self._create_file_fn_git_handler,
        )
        self.sid = sid
        self.event_stream = event_stream
        if event_stream:
            event_stream.subscribe(
                EventStreamSubscriber.RUNTIME, self.on_event, self.sid
            )
        self.plugins = (
            copy.deepcopy(plugins) if plugins is not None and len(plugins) > 0 else []
        )

        # add VSCode plugin if not in headless mode
        if not headless_mode and not DISABLE_VSCODE_PLUGIN:
            self.plugins.append(VSCodeRequirement())
        logger.info(f'Loaded plugins for runtime {self.sid}: {self.plugins}')

        self.status_callback = status_callback
        self.attach_to_existing = attach_to_existing

        self.config = copy.deepcopy(config)
        atexit.register(self.close)

        self.initial_env_vars = _default_env_vars(config.sandbox)
        if env_vars is not None:
            self.initial_env_vars.update(env_vars)

        self.provider_handler = ProviderHandler(
            provider_tokens=git_provider_tokens
            or cast(PROVIDER_TOKEN_TYPE, MappingProxyType({})),
            external_auth_id=user_id,
            external_token_manager=True,
        )
        raw_env_vars: dict[str, str] = call_async_from_sync(
            self.provider_handler.get_env_vars, GENERAL_TIMEOUT, True, None, False
        )
        self.initial_env_vars.update(raw_env_vars)

        self._vscode_enabled = any(
            isinstance(plugin, VSCodeRequirement) for plugin in self.plugins
        )

        # Load mixins
        FileEditRuntimeMixin.__init__(
            self,
            enable_llm_editor=config.get_agent_config().enable_llm_editor,
            llm_registry=llm_registry,
        )

        self.user_id = user_id
        self.git_provider_tokens = git_provider_tokens
        self.runtime_status = None