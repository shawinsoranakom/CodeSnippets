def test_valid_case(self):
        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            fk_name = "parent"

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsValid(TestModelAdmin, ValidationTestModel)