def test_add_auto_field_does_not_request_default(self, mocked_ask_method):
        initial_state = ModelState(
            "testapp",
            "Author",
            [
                ("pkfield", models.IntegerField(primary_key=True)),
            ],
        )
        for auto_field in [
            models.AutoField,
            models.BigAutoField,
            models.SmallAutoField,
        ]:
            with self.subTest(auto_field=auto_field):
                updated_state = ModelState(
                    "testapp",
                    "Author",
                    [
                        ("id", auto_field(primary_key=True)),
                        ("pkfield", models.IntegerField(primary_key=False)),
                    ],
                )
                self.get_changes([initial_state], [updated_state])
                mocked_ask_method.assert_not_called()