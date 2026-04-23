def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            ordering = ("name", "pk")

        self.assertIsValid(TestModelAdmin, ValidationTestModel)