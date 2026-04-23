def test_invalid_model_type(self):
        class SomethingBad:
            pass

        class ValidationTestInline(TabularInline):
            model = SomethingBad

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalidRegexp(
            TestModelAdmin,
            ValidationTestModel,
            r"The value of '.*\.ValidationTestInline.model' must be a Model\.",
            "admin.E106",
        )