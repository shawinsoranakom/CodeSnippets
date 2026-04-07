def test_invalid_field_type(self):
        class TestModelAdmin(ModelAdmin):
            filter_horizontal = ("name",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'filter_horizontal[0]' must be a many-to-many field.",
            "admin.E020",
        )