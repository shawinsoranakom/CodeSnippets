def update_sandbox_config(
        cls,
        openhands_config: OpenHandsConfig,
        base_container_image: str | None,
        runtime_container_image: str | None,
        is_experimental: bool,
    ) -> None:
        if runtime_container_image is not None and base_container_image is not None:
            raise ValueError('Cannot provide both runtime and base container images.')

        if (
            runtime_container_image is None
            and base_container_image is None
            and not is_experimental
        ):
            runtime_container_image = (
                f'ghcr.io/openhands/runtime:{openhands.__version__}-nikolaik'
            )

        # Convert container image values to string or None
        container_base = (
            str(base_container_image) if base_container_image is not None else None
        )
        container_runtime = (
            str(runtime_container_image)
            if runtime_container_image is not None
            else None
        )

        sandbox_config = SandboxConfig(
            base_container_image=container_base,
            runtime_container_image=container_runtime,
            enable_auto_lint=False,
            use_host_network=False,
            timeout=300,
        )

        # Configure sandbox for GitLab CI environment
        if cls.GITLAB_CI:
            sandbox_config.local_runtime_url = os.getenv(
                'LOCAL_RUNTIME_URL', 'http://localhost'
            )
            user_id = os.getuid() if hasattr(os, 'getuid') else 1000
            if user_id == 0:
                sandbox_config.user_id = get_unique_uid()

        openhands_config.sandbox.base_container_image = (
            sandbox_config.base_container_image
        )
        openhands_config.sandbox.runtime_container_image = (
            sandbox_config.runtime_container_image
        )
        openhands_config.sandbox.enable_auto_lint = sandbox_config.enable_auto_lint
        openhands_config.sandbox.use_host_network = sandbox_config.use_host_network
        openhands_config.sandbox.timeout = sandbox_config.timeout
        openhands_config.sandbox.local_runtime_url = sandbox_config.local_runtime_url
        openhands_config.sandbox.user_id = sandbox_config.user_id