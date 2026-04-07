def test_invalid_type(self):
        class FakeFormSet:
            pass

        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            formset = FakeFormSet

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'formset' must inherit from 'BaseModelFormSet'.",
            "admin.E206",
            invalid_obj=ValidationTestInline,
        )