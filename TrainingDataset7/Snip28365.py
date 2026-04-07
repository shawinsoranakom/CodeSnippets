def test_error_messages_overrides(self):
        form = FieldOverridesByFormMetaForm(
            data={
                "name": "Category",
                "url": "http://www.example.com/category/",
                "slug": "!%#*@",
            }
        )
        form.full_clean()

        error = [
            "Didn't you read the help text? "
            "We said letters, numbers, underscores and hyphens only!",
        ]
        self.assertEqual(form.errors, {"slug": error})