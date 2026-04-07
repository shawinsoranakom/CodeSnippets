def test_create_model_with_duplicate_manager_name(self):
        with self.assertRaisesMessage(
            ValueError,
            "Found duplicate value objects in CreateModel managers argument.",
        ):
            migrations.CreateModel(
                "Pony",
                fields=[],
                managers=[
                    ("objects", models.Manager()),
                    ("objects", models.Manager()),
                ],
            )