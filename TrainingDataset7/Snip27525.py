def test_swapping_fields_names(self):
        self.assertDoesNotOptimize(
            [
                migrations.CreateModel(
                    "MyModel",
                    [
                        ("field_a", models.IntegerField()),
                        ("field_b", models.IntegerField()),
                    ],
                ),
                migrations.RunPython(migrations.RunPython.noop),
                migrations.RenameField("MyModel", "field_a", "field_c"),
                migrations.RenameField("MyModel", "field_b", "field_a"),
                migrations.RenameField("MyModel", "field_c", "field_b"),
            ],
        )