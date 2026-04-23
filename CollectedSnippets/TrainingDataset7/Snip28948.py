def test_missing_in_list_display(self):
        class TestModelAdmin(ModelAdmin):
            list_display_links = ("name",)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_display_links[0]' refers to 'name', which is not "
            "defined in 'list_display'.",
            "admin.E111",
        )