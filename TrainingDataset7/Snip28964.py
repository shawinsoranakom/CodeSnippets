def test_not_integer(self):
        class TestModelAdmin(ModelAdmin):
            list_per_page = "hello"

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_per_page' must be an integer.",
            "admin.E118",
        )