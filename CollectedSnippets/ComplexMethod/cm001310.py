def _collect_output_files(self) -> dict[str, str]:
        """Collect output files from workspace for evaluation."""
        outputs: dict[str, str] = {}

        if self._workspace is None:
            return outputs

        # Check agent workspace directory
        agent_workspace = self._workspace / ".autogpt" / "agents"

        # Find agent workspace directory
        if agent_workspace.exists():
            for agent_dir in agent_workspace.iterdir():
                workspace_dir = agent_dir / "workspace"
                if workspace_dir.exists():
                    for file in workspace_dir.rglob("*"):
                        if file.is_file():
                            try:
                                rel_path = file.relative_to(workspace_dir)
                                content = file.read_text(errors="replace")
                                outputs[str(rel_path)] = content
                            except Exception:
                                pass

        # Also check the root workspace for any files created there
        for file in self._workspace.iterdir():
            if file.is_file() and not file.name.startswith("."):
                try:
                    outputs[file.name] = file.read_text(errors="replace")
                except Exception:
                    pass

        return outputs