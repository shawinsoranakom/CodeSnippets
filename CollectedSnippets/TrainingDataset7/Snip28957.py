def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            list_filter = ("non_existent_field",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0]' refers to 'non_existent_field', "
            "which does not refer to a Field.",
            "admin.E116",
        )