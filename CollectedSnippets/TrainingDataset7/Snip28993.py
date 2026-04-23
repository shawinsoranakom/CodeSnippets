def test_missing_model_field(self):
        class ValidationTestInline(TabularInline):
            pass

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalidRegexp(
            TestModelAdmin,
            ValidationTestModel,
            r"'.*\.ValidationTestInline' must have a 'model' attribute\.",
            "admin.E105",
        )