def test_from_path(self, mocker):
        match = object()
        get_new_command = object()
        load_source = mocker.patch(
            'thefuck.types.load_source',
            return_value=Mock(match=match,
                              get_new_command=get_new_command,
                              enabled_by_default=True,
                              priority=900,
                              requires_output=True))
        rule_path = os.path.join(os.sep, 'rules', 'bash.py')
        assert (Rule.from_path(Path(rule_path))
                == Rule('bash', match, get_new_command, priority=900))
        load_source.assert_called_once_with('bash', rule_path)