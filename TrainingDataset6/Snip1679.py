def _compare_names(self, rules, names):
        assert {r.name for r in rules} == set(names)