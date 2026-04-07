def test_not_integer(self):
        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            extra = "hello"

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'extra' must be an integer.",
            "admin.E203",
            invalid_obj=ValidationTestInline,
        )