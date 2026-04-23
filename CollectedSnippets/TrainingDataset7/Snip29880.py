def test_reduce_add_rename(self):
        self.assertOptimizesTo(
            [
                AddIndexConcurrently(
                    "Pony",
                    Index(fields=["pink"], name="pony_pink_idx"),
                ),
                RenameIndex(
                    "Pony",
                    old_name="pony_pink_idx",
                    new_name="pony_pink_index",
                ),
            ],
            [
                AddIndexConcurrently(
                    "Pony",
                    Index(fields=["pink"], name="pony_pink_index"),
                ),
            ],
        )