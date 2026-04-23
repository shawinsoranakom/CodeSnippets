def test_inline(self):
        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            fields = 10

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fields' must be a list or tuple.",
            "admin.E004",
            invalid_obj=ValidationTestInline,
        )