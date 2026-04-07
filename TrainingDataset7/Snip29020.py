def test_autocomplete_e38(self):
        class Admin(ModelAdmin):
            autocomplete_fields = ("name",)

        self.assertIsInvalid(
            Admin,
            ValidationTestModel,
            msg=(
                "The value of 'autocomplete_fields[0]' must be a foreign "
                "key or a many-to-many field."
            ),
            id="admin.E038",
            invalid_obj=Admin,
        )