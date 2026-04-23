def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            list_display = ("non_existent_field",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_display[0]' refers to 'non_existent_field', "
            "which is not a callable or attribute of 'TestModelAdmin', "
            "or an attribute, method, or field on 'modeladmin.ValidationTestModel'.",
            "admin.E108",
        )