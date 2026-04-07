def test_own_alias_dependency(self):
        raw = [("s1", ("s1_db", ["alpha", "bravo"]))]
        dependencies = {"alpha": ["bravo"]}

        with self.assertRaises(ImproperlyConfigured):
            dependency_ordered(raw, dependencies=dependencies)

        # reordering aliases shouldn't matter
        raw = [("s1", ("s1_db", ["bravo", "alpha"]))]

        with self.assertRaises(ImproperlyConfigured):
            dependency_ordered(raw, dependencies=dependencies)