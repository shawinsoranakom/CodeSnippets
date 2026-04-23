def unregister_commands(
        self, registered_commands: Dict[str, List[str]], project_root: Path
    ) -> None:
        """Remove previously registered command files from agent directories.

        Args:
            registered_commands: Dict mapping agent names to command name lists
            project_root: Path to project root
        """
        self._ensure_configs()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in self.AGENT_CONFIGS:
                continue

            agent_config = self.AGENT_CONFIGS[agent_name]
            commands_dir = project_root / agent_config["dir"]

            for cmd_name in cmd_names:
                output_name = self._compute_output_name(
                    agent_name, cmd_name, agent_config
                )
                cmd_file = commands_dir / f"{output_name}{agent_config['extension']}"
                if cmd_file.exists():
                    cmd_file.unlink()
                    # For SKILL.md agents each command lives in its own subdirectory
                    # (e.g. .agents/skills/speckit-ext-cmd/SKILL.md). Remove the
                    # parent dir when it becomes empty to avoid orphaned directories.
                    parent = cmd_file.parent
                    if parent != commands_dir and parent.exists():
                        try:
                            parent.rmdir()  # no-op if dir still has other files
                        except OSError:
                            pass

                if agent_name == "copilot":
                    prompt_file = (
                        project_root / ".github" / "prompts" / f"{cmd_name}.prompt.md"
                    )
                    if prompt_file.exists():
                        prompt_file.unlink()