def test_valid_complex_case(self):
        class TestModelAdmin(ModelAdmin):
            ordering = ("band__name",)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)