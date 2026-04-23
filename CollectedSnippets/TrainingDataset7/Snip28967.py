def test_valid_case(self):
        class TestModelAdmin(ModelAdmin):
            list_max_show_all = 200

        self.assertIsValid(TestModelAdmin, ValidationTestModel)