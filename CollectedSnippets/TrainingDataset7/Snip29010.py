def test_inline_without_formset_class(self):
        class ValidationTestInlineWithoutFormsetClass(TabularInline):
            model = ValidationTestInlineModel
            formset = "Not a FormSet Class"

        class TestModelAdminWithoutFormsetClass(ModelAdmin):
            inlines = [ValidationTestInlineWithoutFormsetClass]

        self.assertIsInvalid(
            TestModelAdminWithoutFormsetClass,
            ValidationTestModel,
            "The value of 'formset' must inherit from 'BaseModelFormSet'.",
            "admin.E206",
            invalid_obj=ValidationTestInlineWithoutFormsetClass,
        )