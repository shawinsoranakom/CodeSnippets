def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            radio_fields = {"state": VERTICAL}

        self.assertIsValid(TestModelAdmin, ValidationTestModel)