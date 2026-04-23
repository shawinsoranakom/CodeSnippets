def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            list_select_related = False

        self.assertIsValid(TestModelAdmin, ValidationTestModel)