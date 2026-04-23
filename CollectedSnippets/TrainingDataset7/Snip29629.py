def test_invalid_default(self):
        class MyModel(PostgreSQLModel):
            field = ArrayField(models.IntegerField(), default=[])

        model = MyModel()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg=(
                        "ArrayField default should be a callable instead of an "
                        "instance so that it's not shared between all field "
                        "instances."
                    ),
                    hint="Use a callable instead, e.g., use `list` instead of `[]`.",
                    obj=MyModel._meta.get_field("field"),
                    id="fields.E010",
                )
            ],
        )