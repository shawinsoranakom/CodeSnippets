def test_get_rules_rule_exception(mocker, glob):
    load_source = mocker.patch('thefuck.types.load_source',
                               side_effect=ImportError("No module named foo..."))
    glob([Path('git.py')])
    assert not corrector.get_rules()
    load_source.assert_called_once_with('git', 'git.py')