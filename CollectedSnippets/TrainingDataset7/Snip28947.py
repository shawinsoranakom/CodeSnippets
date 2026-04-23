def test_missing_field(self):
        class TestModelAdmin(ModelAdmin):
            list_display_links = ("non_existent_field",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            (
                "The value of 'list_display_links[0]' refers to "
                "'non_existent_field', which is not defined in 'list_display'."
            ),
            "admin.E111",
        )