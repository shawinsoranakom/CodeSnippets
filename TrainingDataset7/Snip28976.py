def test_related_invalid_field_type(self):
        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "band__name"

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'date_hierarchy' must be a DateField or DateTimeField.",
            "admin.E128",
        )