def _try_dispatch(
        command: str,
        integration_key: str | None,
        model: str | None,
        args: str,
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Invoke *command* by name through the integration CLI.

        The integration's ``dispatch_command`` builds the native
        slash-command invocation (e.g. ``/speckit.specify`` for
        markdown agents, ``/speckit-specify`` for skills agents),
        then executes the CLI non-interactively.

        Returns the dispatch result dict, or ``None`` if dispatch is
        not possible (integration not found, CLI not installed, or
        dispatch not supported).
        """
        if not integration_key:
            return None

        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            return None

        impl = get_integration(integration_key)
        if impl is None:
            return None

        # Check if the integration supports CLI dispatch
        if impl.build_exec_args("test") is None:
            return None

        # Check if the CLI tool is actually installed
        if not shutil.which(impl.key):
            return None

        project_root = Path(context.project_root) if context.project_root else None

        try:
            return impl.dispatch_command(
                command,
                args=args,
                project_root=project_root,
                model=model,
            )
        except (NotImplementedError, OSError):
            return None