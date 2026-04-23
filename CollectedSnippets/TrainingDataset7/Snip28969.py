def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "non_existent_field"

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'date_hierarchy' refers to 'non_existent_field', "
            "which does not refer to a Field.",
            "admin.E127",
        )