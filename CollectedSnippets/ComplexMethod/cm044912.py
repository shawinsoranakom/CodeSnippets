def test_integration_copilot_creates_files(self, tmp_path):
        from typer.testing import CliRunner
        from specify_cli import app
        runner = CliRunner()
        project = tmp_path / "int-test"
        project.mkdir()
        old_cwd = os.getcwd()
        try:
            os.chdir(project)
            result = runner.invoke(app, [
                "init", "--here", "--integration", "copilot", "--script", "sh", "--no-git",
            ], catch_exceptions=False)
        finally:
            os.chdir(old_cwd)
        assert result.exit_code == 0, f"init failed: {result.output}"
        assert (project / ".github" / "agents" / "speckit.plan.agent.md").exists()
        assert (project / ".github" / "prompts" / "speckit.plan.prompt.md").exists()
        assert (project / ".specify" / "scripts" / "bash" / "common.sh").exists()

        data = json.loads((project / ".specify" / "integration.json").read_text(encoding="utf-8"))
        assert data["integration"] == "copilot"

        opts = json.loads((project / ".specify" / "init-options.json").read_text(encoding="utf-8"))
        assert opts["integration"] == "copilot"
        assert opts["context_file"] == ".github/copilot-instructions.md"

        assert (project / ".specify" / "integrations" / "copilot.manifest.json").exists()

        # Context section should be upserted into the copilot instructions file
        ctx_file = project / ".github" / "copilot-instructions.md"
        assert ctx_file.exists()
        ctx_content = ctx_file.read_text(encoding="utf-8")
        assert "<!-- SPECKIT START -->" in ctx_content
        assert "<!-- SPECKIT END -->" in ctx_content

        shared_manifest = project / ".specify" / "integrations" / "speckit.manifest.json"
        assert shared_manifest.exists()