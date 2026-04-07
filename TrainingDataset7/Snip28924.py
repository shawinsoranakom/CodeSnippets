def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            filter_horizontal = ("users",)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)