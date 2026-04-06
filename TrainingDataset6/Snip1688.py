def test_from_path_rule_exception(self, mocker):
        load_source = mocker.patch('thefuck.types.load_source',
                                   side_effect=ImportError("No module named foo..."))
        assert Rule.from_path(Path('git.py')) is None
        load_source.assert_called_once_with('git', 'git.py')