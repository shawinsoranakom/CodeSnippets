def test_valid_case(self):
        class ValidationTestInline(TabularInline):
            model = ValidationTestInlineModel
            max_num = 2

        class TestModelAdmin(ModelAdmin):
            inlines = [ValidationTestInline]

        self.assertIsValid(TestModelAdmin, ValidationTestModel)