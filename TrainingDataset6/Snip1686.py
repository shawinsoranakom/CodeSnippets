def test_representable(self):
        assert '{}'.format(CorrectedCommand('ls', None, 100)) == \
               'CorrectedCommand(script=ls, side_effect=None, priority=100)'
        assert u'{}'.format(CorrectedCommand(u'echo café', None, 100)) == \
               u'CorrectedCommand(script=echo café, side_effect=None, priority=100)'