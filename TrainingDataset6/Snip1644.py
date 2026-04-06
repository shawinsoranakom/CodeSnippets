def test_to_shell(self, shell):
        assert shell.to_shell('pwd') == 'pwd'