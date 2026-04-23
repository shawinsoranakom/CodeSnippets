def test_invalid_default(self):
        class MyModel(PostgreSQLModel):
            field = HStoreField(default={})

        model = MyModel()
        self.assertEqual(
            model.check(),
            [
                checks.Warning(
                    msg=(
                        "HStoreField default should be a callable instead of an "
                        "instance so that it's not shared between all field "
                        "instances."
                    ),
                    hint="Use a callable instead, e.g., use `dict` instead of `{}`.",
                    obj=MyModel._meta.get_field("field"),
                    id="fields.E010",
                )
            ],
        )