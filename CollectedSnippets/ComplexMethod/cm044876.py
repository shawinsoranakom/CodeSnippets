def test_codex_skill_registration_writes_skill_frontmatter(self, extension_dir, project_dir):
        """Codex SKILL.md output should use skills-oriented frontmatter."""
        skills_dir = project_dir / ".agents" / "skills"
        skills_dir.mkdir(parents=True)

        manifest = ExtensionManifest(extension_dir / "extension.yml")
        registrar = CommandRegistrar()
        registrar.register_commands_for_agent("codex", manifest, extension_dir, project_dir)

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: speckit-test-ext-hello" in content
        assert "description: Test hello command" in content
        assert "compatibility:" in content
        assert "metadata:" in content
        assert "source: test-ext:commands/hello.md" in content
        assert "<!-- Extension:" not in content