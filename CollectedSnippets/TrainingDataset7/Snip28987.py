def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            save_as = True

        self.assertIsValid(TestModelAdmin, ValidationTestModel)