def test_update_failure_rolls_back_registry_hooks_and_commands(self, tmp_path):
        """Failed update should restore original registry, hooks, and command files."""
        from typer.testing import CliRunner
        from unittest.mock import patch
        from specify_cli import app
        import yaml

        runner = CliRunner()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        (project_dir / ".specify").mkdir()
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)
        v1_dir = self._create_extension_source(tmp_path, "1.0.0")
        manager.install_from_directory(v1_dir, "0.1.0")

        backup_registry_entry = manager.registry.get("test-ext")
        hooks_before = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())

        registered_commands = backup_registry_entry.get("registered_commands", {})
        command_files = []
        from specify_cli.agents import CommandRegistrar as AgentRegistrar
        agent_registrar = AgentRegistrar()
        for agent_name, cmd_names in registered_commands.items():
            if agent_name not in agent_registrar.AGENT_CONFIGS:
                continue
            agent_cfg = agent_registrar.AGENT_CONFIGS[agent_name]
            commands_dir = project_dir / agent_cfg["dir"]
            for cmd_name in cmd_names:
                output_name = AgentRegistrar._compute_output_name(agent_name, cmd_name, agent_cfg)
                cmd_path = commands_dir / f"{output_name}{agent_cfg['extension']}"
                command_files.append(cmd_path)

        assert command_files, "Expected at least one registered command file"
        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to exist before update: {cmd_file}"

        zip_path = tmp_path / "test-ext-update.zip"
        self._create_catalog_zip(zip_path, "2.0.0")

        with patch.object(Path, "cwd", return_value=project_dir), \
             patch.object(ExtensionCatalog, "get_extension_info", return_value={
                 "id": "test-ext",
                 "name": "Test Extension",
                 "version": "2.0.0",
                 "_install_allowed": True,
             }), \
             patch.object(ExtensionCatalog, "download_extension", return_value=zip_path), \
             patch.object(ExtensionManager, "install_from_zip", side_effect=RuntimeError("install failed")):
            result = runner.invoke(app, ["extension", "update", "test-ext"], input="y\n", catch_exceptions=True)

        assert result.exit_code == 1, result.output

        restored_entry = ExtensionManager(project_dir).registry.get("test-ext")
        assert restored_entry == backup_registry_entry

        hooks_after = yaml.safe_load((project_dir / ".specify" / "extensions.yml").read_text())
        assert hooks_after == hooks_before

        for cmd_file in command_files:
            assert cmd_file.exists(), f"Expected command file to be restored after rollback: {cmd_file}"