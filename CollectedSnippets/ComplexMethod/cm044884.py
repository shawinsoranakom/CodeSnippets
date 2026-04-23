def test_wrap_aliases_are_replayed_and_removed(self, project_dir, temp_dir):
        """Replay preserves wrap aliases across install/remove lifecycle changes."""
        from specify_cli.agents import CommandRegistrar
        import copy

        core_dir = project_dir / ".specify" / "templates" / "commands"
        core_dir.mkdir(parents=True, exist_ok=True)
        (core_dir / "specify.md").write_text("---\ndescription: core\n---\n\nCORE\n")

        registrar = CommandRegistrar()
        original = copy.deepcopy(registrar.AGENT_CONFIGS)
        agent_dir = project_dir / ".claude" / "commands"
        agent_dir.mkdir(parents=True, exist_ok=True)
        registrar.AGENT_CONFIGS["test-agent"] = {
            "dir": str(agent_dir.relative_to(project_dir)),
            "format": "markdown", "args": "$ARGUMENTS",
            "extension": ".md", "strip_frontmatter_keys": [],
        }
        try:
            manager = PresetManager(project_dir)
            outer_src = _make_wrap_preset_dir(
                temp_dir,
                "preset-outer",
                "speckit.specify",
                "OUTER-PRE",
                "OUTER-POST",
                aliases=["speckit.alias"],
            )
            inner_src = _make_wrap_preset_dir(
                temp_dir, "preset-inner", "speckit.specify", "INNER-PRE", "INNER-POST"
            )
            manager.install_from_directory(outer_src, "0.1.0", priority=5)
            manager.install_from_directory(inner_src, "0.1.0", priority=10)

            alias_file = agent_dir / "speckit.alias.md"
            written = alias_file.read_text()
            assert "OUTER-PRE" in written
            assert "INNER-PRE" in written
            assert "INNER-POST" in written
            assert "OUTER-POST" in written

            manager.remove("preset-inner")
            written = alias_file.read_text()
            assert "OUTER-PRE" in written
            assert "OUTER-POST" in written
            assert "INNER-PRE" not in written
            assert "INNER-POST" not in written

            manager.remove("preset-outer")
        finally:
            CommandRegistrar.AGENT_CONFIGS.clear()
            CommandRegistrar.AGENT_CONFIGS.update(original)

        assert not (agent_dir / "speckit.alias.md").exists()