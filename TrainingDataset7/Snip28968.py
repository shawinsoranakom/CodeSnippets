def test_not_iterable(self):
        class TestModelAdmin(ModelAdmin):
            search_fields = 10

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'search_fields' must be a list or tuple.",
            "admin.E126",
        )