def test_invalid_type(self):
        class TestModelAdmin(ModelAdmin):
            list_select_related = 1

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_select_related' must be a boolean, tuple or list.",
            "admin.E117",
        )