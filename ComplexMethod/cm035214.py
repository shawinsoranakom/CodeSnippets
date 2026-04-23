def config_from_env() -> AppServerConfig:
    # Import defaults...
    from openhands.app_server.app_conversation.live_status_app_conversation_service import (  # noqa: E501
        LiveStatusAppConversationServiceInjector,
    )
    from openhands.app_server.app_conversation.sql_app_conversation_info_service import (  # noqa: E501
        SQLAppConversationInfoServiceInjector,
    )
    from openhands.app_server.app_conversation.sql_app_conversation_start_task_service import (  # noqa: E501
        SQLAppConversationStartTaskServiceInjector,
    )
    from openhands.app_server.event.aws_event_service import (
        AwsEventServiceInjector,
    )
    from openhands.app_server.event.filesystem_event_service import (
        FilesystemEventServiceInjector,
    )
    from openhands.app_server.event.google_cloud_event_service import (
        GoogleCloudEventServiceInjector,
    )
    from openhands.app_server.event_callback.sql_event_callback_service import (
        SQLEventCallbackServiceInjector,
    )
    from openhands.app_server.sandbox.docker_sandbox_service import (
        DockerSandboxServiceInjector,
    )
    from openhands.app_server.sandbox.docker_sandbox_spec_service import (
        DockerSandboxSpecServiceInjector,
    )
    from openhands.app_server.sandbox.process_sandbox_service import (
        ProcessSandboxServiceInjector,
    )
    from openhands.app_server.sandbox.process_sandbox_spec_service import (
        ProcessSandboxSpecServiceInjector,
    )
    from openhands.app_server.sandbox.remote_sandbox_service import (
        RemoteSandboxServiceInjector,
    )
    from openhands.app_server.sandbox.remote_sandbox_spec_service import (
        RemoteSandboxSpecServiceInjector,
    )
    from openhands.app_server.user.auth_user_context import (
        AuthUserContextInjector,
    )

    config: AppServerConfig = from_env(AppServerConfig, 'OH')  # type: ignore

    if config.event is None:
        provider = get_storage_provider()

        if provider == StorageProvider.AWS:
            # AWS S3 storage configuration
            bucket_name = os.environ.get('FILE_STORE_PATH')
            if not bucket_name:
                raise ValueError(
                    'FILE_STORE_PATH environment variable is required for S3 storage'
                )
            config.event = AwsEventServiceInjector(bucket_name=bucket_name)
        elif provider == StorageProvider.GCP:
            # Google Cloud storage configuration
            bucket_name = os.environ.get('FILE_STORE_PATH')
            if not bucket_name:
                raise ValueError(
                    'FILE_STORE_PATH environment variable is required for Google Cloud storage'
                )
            config.event = GoogleCloudEventServiceInjector(bucket_name=bucket_name)
        else:
            config.event = FilesystemEventServiceInjector()

    if config.event_callback is None:
        config.event_callback = SQLEventCallbackServiceInjector()

    if config.sandbox is None:
        # Legacy fallback
        if os.getenv('RUNTIME') == 'remote':
            config.sandbox = RemoteSandboxServiceInjector(
                api_key=os.environ['SANDBOX_API_KEY'],
                api_url=os.environ['SANDBOX_REMOTE_RUNTIME_API_URL'],
            )
        elif os.getenv('RUNTIME') in ('local', 'process'):
            config.sandbox = ProcessSandboxServiceInjector()
        else:
            # Support legacy environment variables for Docker sandbox configuration
            docker_sandbox_kwargs: dict = {}
            if os.getenv('SANDBOX_HOST_PORT'):
                docker_sandbox_kwargs['host_port'] = int(
                    os.environ['SANDBOX_HOST_PORT']
                )
            if os.getenv('SANDBOX_CONTAINER_URL_PATTERN'):
                docker_sandbox_kwargs['container_url_pattern'] = os.environ[
                    'SANDBOX_CONTAINER_URL_PATTERN'
                ]
            # Allow configuring sandbox startup grace period
            # This is useful for slower machines or cloud environments where
            # the agent-server container takes longer to initialize
            if os.getenv('SANDBOX_STARTUP_GRACE_SECONDS'):
                docker_sandbox_kwargs['startup_grace_seconds'] = int(
                    os.environ['SANDBOX_STARTUP_GRACE_SECONDS']
                )
            # Parse SANDBOX_VOLUMES and convert to VolumeMount objects
            # This is set by the CLI's --mount-cwd flag
            sandbox_volumes = os.getenv('SANDBOX_VOLUMES')
            if sandbox_volumes:
                from openhands.app_server.sandbox.docker_sandbox_service import (
                    VolumeMount,
                )

                mounts = []
                for mount_spec in sandbox_volumes.split(','):
                    mount_spec = mount_spec.strip()
                    if not mount_spec:
                        continue
                    parts = mount_spec.split(':')
                    if len(parts) >= 2:
                        host_path = parts[0]
                        container_path = parts[1]
                        mode = parts[2] if len(parts) > 2 else 'rw'
                        mounts.append(
                            VolumeMount(
                                host_path=host_path,
                                container_path=container_path,
                                mode=mode,
                            )
                        )
                if mounts:
                    docker_sandbox_kwargs['mounts'] = mounts
            config.sandbox = DockerSandboxServiceInjector(**docker_sandbox_kwargs)

    if config.sandbox_spec is None:
        if os.getenv('RUNTIME') == 'remote':
            config.sandbox_spec = RemoteSandboxSpecServiceInjector()
        elif os.getenv('RUNTIME') in ('local', 'process'):
            config.sandbox_spec = ProcessSandboxSpecServiceInjector()
        else:
            config.sandbox_spec = DockerSandboxSpecServiceInjector()

    if config.app_conversation_info is None:
        config.app_conversation_info = SQLAppConversationInfoServiceInjector()

    if config.app_conversation_start_task is None:
        config.app_conversation_start_task = (
            SQLAppConversationStartTaskServiceInjector()
        )

    if config.app_conversation is None:
        tavily_api_key = None
        tavily_api_key_str = os.getenv('TAVILY_API_KEY') or os.getenv('SEARCH_API_KEY')
        if tavily_api_key_str:
            tavily_api_key = SecretStr(tavily_api_key_str)
        config.app_conversation = LiveStatusAppConversationServiceInjector(
            tavily_api_key=tavily_api_key
        )

    if config.pending_message is None:
        from openhands.app_server.pending_messages.pending_message_service import (
            SQLPendingMessageServiceInjector,
        )

        config.pending_message = SQLPendingMessageServiceInjector()

    if config.user is None:
        config.user = AuthUserContextInjector()

    if config.jwt is None:
        config.jwt = JwtServiceInjector(persistence_dir=config.persistence_dir)

    return config