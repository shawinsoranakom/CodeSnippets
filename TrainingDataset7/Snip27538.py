def test_add_remove_index(self):
        self.assertOptimizesTo(
            [
                migrations.AddIndex(
                    "Pony",
                    models.Index(
                        fields=["weight", "pink"], name="idx_pony_weight_pink"
                    ),
                ),
                migrations.RemoveIndex("Pony", "idx_pony_weight_pink"),
            ],
            [],
        )