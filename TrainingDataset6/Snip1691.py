def test_is_enabled(self, settings, rules, rule, is_enabled):
        settings.update(rules=rules)
        assert rule.is_enabled == is_enabled