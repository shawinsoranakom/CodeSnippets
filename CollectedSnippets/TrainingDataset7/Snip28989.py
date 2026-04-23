def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            save_on_top = True

        self.assertIsValid(TestModelAdmin, ValidationTestModel)