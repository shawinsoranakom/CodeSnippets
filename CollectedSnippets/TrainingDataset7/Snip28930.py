def test_not_list_or_tuple(self):
        class TestModelAdmin(ModelAdmin):
            prepopulated_fields = {"slug": "test"}

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'prepopulated_fields[\"slug\"]' must be a list or tuple.",
            "admin.E029",
        )