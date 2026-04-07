def test_not_integer(self):
        class TestModelAdmin(ModelAdmin):
            list_max_show_all = "hello"

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_max_show_all' must be an integer.",
            "admin.E119",
        )