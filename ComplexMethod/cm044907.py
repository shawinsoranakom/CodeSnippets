def test_toml_triple_double_and_single_quote_ending(self, tmp_path, monkeypatch):
        """Body containing `\"\"\"` and ending with `'` falls back to escaped basic string."""
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Test\n"
            "scripts:\n"
            "  sh: echo ok\n"
            "---\n"
            'Use """triple""" quotes\n'
            "and end with 'single'\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        raw = cmd_files[0].read_text(encoding="utf-8")
        assert "''''" not in raw, (
            "literal string must not produce ambiguous closing quotes"
        )
        parsed = tomllib.loads(raw)
        assert parsed["prompt"].endswith("'single'")
        assert '"""triple"""' in parsed["prompt"]
        assert not parsed["prompt"].endswith("\n"), (
            "parsed value must not gain a trailing newline"
        )