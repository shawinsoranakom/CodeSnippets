def _try_dispatch(
        prompt: str,
        integration_key: str | None,
        model: str | None,
        context: StepContext,
    ) -> dict[str, Any] | None:
        """Dispatch *prompt* directly through the integration CLI."""
        if not integration_key or not prompt:
            return None

        try:
            from specify_cli.integrations import get_integration
        except ImportError:
            return None

        impl = get_integration(integration_key)
        if impl is None:
            return None

        exec_args = impl.build_exec_args(prompt, model=model, output_json=False)
        if exec_args is None:
            return None

        if not shutil.which(impl.key):
            return None

        import subprocess

        project_root = (
            Path(context.project_root) if context.project_root else Path.cwd()
        )

        try:
            result = subprocess.run(
                exec_args,
                text=True,
                cwd=str(project_root),
            )
            return {
                "exit_code": result.returncode,
                "stdout": "",
                "stderr": "",
            }
        except KeyboardInterrupt:
            return {
                "exit_code": 130,
                "stdout": "",
                "stderr": "Interrupted by user",
            }
        except OSError:
            return None