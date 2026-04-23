def test_not_list_filter_class(self):
        class TestModelAdmin(ModelAdmin):
            list_filter = ["RandomClass"]

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'list_filter[0]' refers to 'RandomClass', which "
            "does not refer to a Field.",
            "admin.E116",
        )