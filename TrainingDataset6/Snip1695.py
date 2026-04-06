def test_get_corrected_commands_with_rule_returns_list(self):
        rule = Rule(get_new_command=lambda x: [x.script + '!', x.script + '@'],
                    priority=100)
        assert (list(rule.get_corrected_commands(Command('test', '')))
                == [CorrectedCommand(script='test!', priority=100),
                    CorrectedCommand(script='test@', priority=200)])