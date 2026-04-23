def test_uninstall_removes_files(self, tmp_path):
        project = _init_project(tmp_path, "claude")
        # Claude uses skills directory
        assert (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()
        assert (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0
        assert "uninstalled" in result.output

        # Command files removed
        assert not (project / ".claude" / "skills" / "speckit-plan" / "SKILL.md").exists()

        # Manifest removed
        assert not (project / ".specify" / "integrations" / "claude.manifest.json").exists()

        # integration.json removed
        assert not (project / ".specify" / "integration.json").exists()