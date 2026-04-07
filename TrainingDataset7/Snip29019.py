def test_autocomplete_e037(self):
        class Admin(ModelAdmin):
            autocomplete_fields = ("nonexistent",)

        self.assertIsInvalid(
            Admin,
            ValidationTestModel,
            msg=(
                "The value of 'autocomplete_fields[0]' refers to 'nonexistent', "
                "which is not a field of 'modeladmin.ValidationTestModel'."
            ),
            id="admin.E037",
            invalid_obj=Admin,
        )