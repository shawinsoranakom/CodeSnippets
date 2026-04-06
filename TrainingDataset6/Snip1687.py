def test_run(self, capsys, settings, script, printed, override_settings):
        settings.update(override_settings)
        CorrectedCommand(script, None, 1000).run(Command(script, ''))
        out, _ = capsys.readouterr()
        assert out == printed