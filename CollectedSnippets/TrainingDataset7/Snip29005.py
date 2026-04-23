def test_not_integer(self):
        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            max_num = "hello"

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'max_num' must be an integer.",
            "admin.E204",
            invalid_obj=ValidationTestInline,
        )