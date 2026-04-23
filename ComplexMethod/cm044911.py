def test_install_modify_uninstall_preserves_modified(self, tmp_path):
        """Full lifecycle: install → modify file → uninstall → verify modified file kept."""
        project = tmp_path / "lifecycle"
        project.mkdir()
        (project / ".specify").mkdir()

        old_cwd = os.getcwd()
        try:
            os.chdir(project)

            # Install
            result = runner.invoke(app, [
                "integration", "install", "claude",
                "--script", "sh",
            ], catch_exceptions=False)
            assert result.exit_code == 0
            assert "installed successfully" in result.output

            # Claude uses skills directory
            plan_file = project / ".claude" / "skills" / "speckit-plan" / "SKILL.md"
            assert plan_file.exists()

            # Modify one file
            plan_file.write_text("# user customization\n", encoding="utf-8")

            # Uninstall
            result = runner.invoke(app, ["integration", "uninstall"], catch_exceptions=False)
            assert result.exit_code == 0
            assert "preserved" in result.output

            # Modified file kept
            assert plan_file.exists()
            assert plan_file.read_text(encoding="utf-8") == "# user customization\n"
        finally:
            os.chdir(old_cwd)