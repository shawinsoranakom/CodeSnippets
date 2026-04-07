def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            date_hierarchy = "pub_date"

        self.assertIsValid(TestModelAdmin, ValidationTestModel)