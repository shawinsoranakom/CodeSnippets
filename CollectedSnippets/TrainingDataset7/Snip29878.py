def test_reduce_add_remove_concurrently(self):
        self.assertOptimizesTo(
            [
                AddIndexConcurrently(
                    "Pony",
                    Index(fields=["pink"], name="pony_pink_idx"),
                ),
                RemoveIndex("Pony", "pony_pink_idx"),
            ],
            [],
        )