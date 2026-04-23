def test_not_model_admin(self):
        class ValidationTestInline:
            pass

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalidRegexp(
            TestModelAdmin,
            ValidationTestModel,
            r"'.*\.ValidationTestInline' must inherit from 'InlineModelAdmin'\.",
            "admin.E104",
        )