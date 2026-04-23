def test_toml_prompt_excludes_frontmatter(self, tmp_path, monkeypatch):
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Summary line one\n"
            "scripts:\n"
            "  sh: scripts/bash/example.sh\n"
            "---\n"
            "Body line one\n"
            "Body line two\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        generated = cmd_files[0].read_text(encoding="utf-8")
        parsed = tomllib.loads(generated)

        assert parsed["description"] == "Summary line one"
        assert parsed["prompt"] == "Body line one\nBody line two"
        assert "description:" not in parsed["prompt"]
        assert "scripts:" not in parsed["prompt"]
        assert "---" not in parsed["prompt"]