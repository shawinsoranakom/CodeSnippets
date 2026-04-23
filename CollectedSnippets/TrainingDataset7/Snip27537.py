def test_add_rename_index(self):
        tests = [
            models.Index(fields=["weight", "pink"], name="mid_name"),
            models.Index(Abs("weight"), name="mid_name"),
            models.Index(
                Abs("weight"), name="mid_name", condition=models.Q(weight__gt=0)
            ),
        ]
        for index in tests:
            with self.subTest(index=index):
                renamed_index = index.clone()
                renamed_index.name = "new_name"
                self.assertOptimizesTo(
                    [
                        migrations.AddIndex("Pony", index),
                        migrations.RenameIndex(
                            "Pony", new_name="new_name", old_name="mid_name"
                        ),
                    ],
                    [
                        migrations.AddIndex("Pony", renamed_index),
                    ],
                )
                self.assertDoesNotOptimize(
                    [
                        migrations.AddIndex("Pony", index),
                        migrations.RenameIndex(
                            "Pony", new_name="new_name", old_name="other_name"
                        ),
                    ],
                )