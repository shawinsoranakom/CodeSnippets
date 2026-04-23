def test_toml_no_ambiguous_closing_quotes(self, tmp_path, monkeypatch):
        """Multiline body ending with a double quote must not produce an ambiguous TOML multiline-string closing delimiter (#2113)."""
        i = get_integration(self.KEY)
        template = tmp_path / "sample.md"
        template.write_text(
            "---\n"
            "description: Test\n"
            "scripts:\n"
            "  sh: echo ok\n"
            "---\n"
            "Check the following:\n"
            '- Correct: "Is X clearly specified?"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(i, "list_command_templates", lambda: [template])

        m = IntegrationManifest(self.KEY, tmp_path)
        created = i.setup(tmp_path, m)
        cmd_files = [f for f in created if "scripts" not in f.parts]
        assert len(cmd_files) == 1

        raw = cmd_files[0].read_text(encoding="utf-8")
        assert '""""' not in raw, "closing delimiter must not merge with body quote"
        assert '"""\n' in raw, "body must use multiline basic string"
        parsed = tomllib.loads(raw)
        assert parsed["prompt"].endswith('specified?"')
        assert not parsed["prompt"].endswith("\n"), (
            "parsed value must not gain a trailing newline"
        )