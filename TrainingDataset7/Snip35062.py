def test_multiple_dependencies(self):
        raw = [
            ("s1", ("s1_db", ["alpha"])),
            ("s2", ("s2_db", ["bravo"])),
            ("s3", ("s3_db", ["charlie"])),
            ("s4", ("s4_db", ["delta"])),
        ]
        dependencies = {
            "alpha": ["bravo", "delta"],
            "bravo": ["charlie"],
            "delta": ["charlie"],
        }

        ordered = dependency_ordered(raw, dependencies=dependencies)
        ordered_sigs = [sig for sig, aliases in ordered]

        self.assertIn("s1", ordered_sigs)
        self.assertIn("s2", ordered_sigs)
        self.assertIn("s3", ordered_sigs)
        self.assertIn("s4", ordered_sigs)

        # Explicit dependencies
        self.assertLess(ordered_sigs.index("s2"), ordered_sigs.index("s1"))
        self.assertLess(ordered_sigs.index("s4"), ordered_sigs.index("s1"))
        self.assertLess(ordered_sigs.index("s3"), ordered_sigs.index("s2"))
        self.assertLess(ordered_sigs.index("s3"), ordered_sigs.index("s4"))

        # Implicit dependencies
        self.assertLess(ordered_sigs.index("s3"), ordered_sigs.index("s1"))