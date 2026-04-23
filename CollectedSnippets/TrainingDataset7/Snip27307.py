def test_create_model_inheritance(self):
        """
        Tests the CreateModel operation on a multi-table inheritance setup.
        """
        project_state = self.set_up_test_model("test_crmoih")
        # Test the state alteration
        operation = migrations.CreateModel(
            "ShetlandPony",
            [
                (
                    "pony_ptr",
                    models.OneToOneField(
                        "test_crmoih.Pony",
                        models.CASCADE,
                        auto_created=True,
                        primary_key=True,
                        to_field="id",
                        serialize=False,
                    ),
                ),
                ("cuteness", models.IntegerField(default=1)),
            ],
        )
        new_state = project_state.clone()
        operation.state_forwards("test_crmoih", new_state)
        self.assertIn(("test_crmoih", "shetlandpony"), new_state.models)
        # Test the database alteration
        self.assertTableNotExists("test_crmoih_shetlandpony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmoih", editor, project_state, new_state)
        self.assertTableExists("test_crmoih_shetlandpony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_crmoih", editor, new_state, project_state
            )
        self.assertTableNotExists("test_crmoih_shetlandpony")