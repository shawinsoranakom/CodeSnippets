def test_circular_dependencies(self):
        raw = [
            ("s1", ("s1_db", ["alpha"])),
            ("s2", ("s2_db", ["bravo"])),
        ]
        dependencies = {
            "bravo": ["alpha"],
            "alpha": ["bravo"],
        }

        with self.assertRaises(ImproperlyConfigured):
            dependency_ordered(raw, dependencies=dependencies)