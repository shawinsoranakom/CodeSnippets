def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            prepopulated_fields = {"slug": ("name",)}

        self.assertIsValid(TestModelAdmin, ValidationTestModel)