def test_not_iterable(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = 10

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fieldsets' must be a list or tuple.",
            "admin.E007",
        )