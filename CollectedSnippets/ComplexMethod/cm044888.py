def test_skill_md_content_correct(self, skills_project, extension_dir):
        """SKILL.md should have correct agentskills.io structure."""
        project_dir, skills_dir = skills_project
        manager = ExtensionManager(project_dir)
        manager.install_from_directory(
            extension_dir, "0.1.0", register_commands=False
        )

        skill_file = skills_dir / "speckit-test-ext-hello" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()

        # Check structure
        assert content.startswith("---\n")
        assert "name: speckit-test-ext-hello" in content
        assert "description:" in content
        assert "Test hello command" in content
        assert "source: extension:test-ext" in content
        assert "author: github-spec-kit" in content
        assert "compatibility:" in content
        assert "Run this to say hello." in content