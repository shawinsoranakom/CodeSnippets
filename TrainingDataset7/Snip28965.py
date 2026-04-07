def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            list_per_page = 100

        self.assertIsValid(TestModelAdmin, ValidationTestModel)