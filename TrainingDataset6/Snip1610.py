def test_from_shell(self, shell):
        assert shell.from_shell('pwd') == 'pwd'