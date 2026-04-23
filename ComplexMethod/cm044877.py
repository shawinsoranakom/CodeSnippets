def test_full_install_and_remove_workflow(self, extension_dir, project_dir):
        """Test complete installation and removal workflow."""
        # Create Claude directory
        (project_dir / ".claude" / "skills").mkdir(parents=True)

        manager = ExtensionManager(project_dir)

        # Install
        manager.install_from_directory(
            extension_dir,
            "0.1.0",
            register_commands=True
        )

        # Verify installation
        assert manager.registry.is_installed("test-ext")
        installed = manager.list_installed()
        assert len(installed) == 1
        assert installed[0]["id"] == "test-ext"

        # Verify command registered
        cmd_file = project_dir / ".claude" / "skills" / "speckit-test-ext-hello" / "SKILL.md"
        assert cmd_file.exists()

        # Verify registry has registered commands (now a dict keyed by agent)
        metadata = manager.registry.get("test-ext")
        registered_commands = metadata["registered_commands"]
        # Check that the command is registered for at least one agent
        assert any(
            "speckit.test-ext.hello" in cmds
            for cmds in registered_commands.values()
        )

        # Remove
        result = manager.remove("test-ext")
        assert result is True

        # Verify removal
        assert not manager.registry.is_installed("test-ext")
        assert not cmd_file.exists()
        assert len(manager.list_installed()) == 0