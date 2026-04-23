def test_reduce_add_remove(self):
        self.assertOptimizesTo(
            [
                AddIndexConcurrently(
                    "Pony",
                    Index(fields=["pink"], name="pony_pink_idx"),
                ),
                RemoveIndexConcurrently("Pony", "pony_pink_idx"),
            ],
            [],
        )