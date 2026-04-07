def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            raw_id_fields = ("users",)

        self.assertIsValid(TestModelAdmin, ValidationTestModel)