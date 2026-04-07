def test_None_is_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            list_display_links = None

        self.assertIsValid(TestModelAdmin, ValidationTestModel)