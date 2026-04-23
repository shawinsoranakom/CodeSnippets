def dispatch_command(
        self,
        command_name: str,
        args: str = "",
        *,
        project_root: Path | None = None,
        model: str | None = None,
        timeout: int = 600,
        stream: bool = True,
    ) -> dict[str, Any]:
        """Dispatch via ``--agent speckit.<stem>`` instead of slash-commands.

        Copilot ``.agent.md`` files are agents, not skills.  The CLI
        selects them with ``--agent <name>`` and the prompt is just
        the user's arguments.
        """
        import subprocess

        stem = command_name
        if "." in stem:
            stem = stem.rsplit(".", 1)[-1]
        agent_name = f"speckit.{stem}"

        prompt = args or ""
        cli_args = [
            "copilot", "-p", prompt,
            "--agent", agent_name,
        ]
        if _allow_all():
            cli_args.append("--yolo")
        if model:
            cli_args.extend(["--model", model])
        if not stream:
            cli_args.extend(["--output-format", "json"])

        cwd = str(project_root) if project_root else None

        if stream:
            try:
                result = subprocess.run(
                    cli_args,
                    text=True,
                    cwd=cwd,
                )
            except KeyboardInterrupt:
                return {
                    "exit_code": 130,
                    "stdout": "",
                    "stderr": "Interrupted by user",
                }
            return {
                "exit_code": result.returncode,
                "stdout": "",
                "stderr": "",
            }

        result = subprocess.run(
            cli_args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }