def test_isnt_match_when_rule_failed(self, capsys):
        rule = Rule('test', Mock(side_effect=OSError('Denied')),
                    requires_output=False)
        assert not rule.is_match(Command('ls', ''))
        assert capsys.readouterr()[1].split('\n')[0] == '[WARN] Rule test:'