def test_related_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "band__sign_date"

        self.assertIsValid(TestModelAdmin, ValidationTestModel)