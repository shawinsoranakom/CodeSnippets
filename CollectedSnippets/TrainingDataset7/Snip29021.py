def test_autocomplete_e039(self):
        class Admin(ModelAdmin):
            autocomplete_fields = ("band",)

        self.assertIsInvalid(
            Admin,
            Song,
            msg=(
                'An admin for model "Band" has to be registered '
                "to be referenced by Admin.autocomplete_fields."
            ),
            id="admin.E039",
            invalid_obj=Admin,
        )