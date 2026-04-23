def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            filter_horizontal = ("non_existent_field",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'filter_horizontal[0]' refers to 'non_existent_field', "
            "which is not a field of 'modeladmin.ValidationTestModel'.",
            "admin.E019",
        )