def test_valid_random_marker_case(self):
        class TestModelAdmin(ModelAdmin):
            ordering = ("?",)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)