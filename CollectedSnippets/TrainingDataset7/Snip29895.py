def test_reduce_create_remove(self):
        self.assertOptimizesTo(
            [
                CreateCollation(
                    "sample_collation",
                    "und-u-ks-level2",
                    provider="icu",
                    deterministic=False,
                ),
                RemoveCollation(
                    "sample_collation",
                    # Different locale
                    "de-u-ks-level1",
                ),
            ],
            [],
        )