def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            filter_vertical = ("users",)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)