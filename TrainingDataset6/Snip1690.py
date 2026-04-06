def test_from_path_excluded_rule(self, mocker, settings):
        load_source = mocker.patch('thefuck.types.load_source')
        settings.update(exclude_rules=['git'])
        rule_path = os.path.join(os.sep, 'rules', 'git.py')
        assert Rule.from_path(Path(rule_path)) is None
        assert not load_source.called