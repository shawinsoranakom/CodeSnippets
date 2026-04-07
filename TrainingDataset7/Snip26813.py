def test_add_fk_before_generated_field(self):
        initial_state = ModelState(
            "testapp",
            "Author",
            [
                ("name", models.CharField(max_length=20)),
            ],
        )
        updated_state = [
            ModelState(
                "testapp",
                "Publisher",
                [
                    ("name", models.CharField(max_length=20)),
                ],
            ),
            ModelState(
                "testapp",
                "Author",
                [
                    ("name", models.CharField(max_length=20)),
                    (
                        "publisher",
                        models.ForeignKey("testapp.Publisher", models.CASCADE),
                    ),
                    (
                        "lower_full_name",
                        models.GeneratedField(
                            expression=Concat("name", "publisher_id"),
                            output_field=models.CharField(max_length=20),
                            db_persist=True,
                        ),
                    ),
                ],
            ),
        ]
        changes = self.get_changes([initial_state], updated_state)
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes, "testapp", 0, ["CreateModel", "AddField", "AddField"]
        )
        self.assertOperationFieldAttributes(
            changes, "testapp", 0, 2, expression=Concat("name", "publisher_id")
        )