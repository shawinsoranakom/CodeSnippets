def test_create_model_with_duplicate_field_name(self):
        with self.assertRaisesMessage(
            ValueError, "Found duplicate value pink in CreateModel fields argument."
        ):
            migrations.CreateModel(
                "Pony",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("pink", models.TextField()),
                    ("pink", models.IntegerField(default=1)),
                ],
            )