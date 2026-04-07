def test_create_model_rename_index_no_old_fields(self):
        self.assertOptimizesTo(
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                        ("age", models.IntegerField()),
                    ],
                    options={
                        "indexes": [models.Index(fields=["age"], name="idx_pony_age")],
                    },
                ),
                migrations.RenameIndex(
                    "Pony", new_name="idx_pony_age_new", old_name="idx_pony_age"
                ),
            ],
            [
                migrations.CreateModel(
                    name="Pony",
                    fields=[
                        ("weight", models.IntegerField()),
                        ("age", models.IntegerField()),
                    ],
                    options={
                        "indexes": [models.Index(fields=["age"], name="idx_pony_age")],
                    },
                ),
                migrations.RenameIndex(
                    "Pony", new_name="idx_pony_age_new", old_name="idx_pony_age"
                ),
            ],
        )