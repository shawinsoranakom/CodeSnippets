def test_equality(self):
        assert (CorrectedCommand('ls', None, 100) ==
                CorrectedCommand('ls', None, 200))
        assert (CorrectedCommand('ls', None, 100) !=
                CorrectedCommand('ls', lambda *_: _, 100))