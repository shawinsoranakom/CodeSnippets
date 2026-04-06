def test_from_shell(self, before, after, shell):
        assert shell.from_shell(before) == after