def test_with_confirmation_select_second(self, capsys, patch_get_key, commands):
        patch_get_key([const.KEY_DOWN, '\n'])
        assert ui.select_command(iter(commands)) == commands[1]
        stderr = (
            u'{mark}\x1b[1K\rls [enter/↑/↓/ctrl+c]'
            u'{mark}\x1b[1K\rcd [enter/↑/↓/ctrl+c]\n'
        ).format(mark=const.USER_COMMAND_MARK)
        assert capsys.readouterr() == ('', stderr)