def test_add_field_before_generated_field(self):
        initial_state = ModelState(
            "testapp",
            "Author",
            [
                ("name", models.CharField(max_length=20)),
            ],
        )
        updated_state = ModelState(
            "testapp",
            "Author",
            [
                ("name", models.CharField(max_length=20)),
                ("surname", models.CharField(max_length=20)),
                (
                    "lower_full_name",
                    models.GeneratedField(
                        expression=Concat(Lower("name"), Lower("surname")),
                        output_field=models.CharField(max_length=30),
                        db_persist=True,
                    ),
                ),
            ],
        )
        changes = self.get_changes([initial_state], [updated_state])
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AddField", "AddField"])
        self.assertOperationFieldAttributes(
            changes, "testapp", 0, 1, expression=Concat(Lower("name"), Lower("surname"))
        )