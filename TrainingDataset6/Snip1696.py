def test_get_corrected_commands_with_rule_returns_command(self):
        rule = Rule(get_new_command=lambda x: x.script + '!',
                    priority=100)
        assert (list(rule.get_corrected_commands(Command('test', '')))
                == [CorrectedCommand(script='test!', priority=100)])