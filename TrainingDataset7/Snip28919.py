def test_not_iterable(self):
        class TestModelAdmin(ModelAdmin):
            filter_horizontal = 10

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'filter_horizontal' must be a list or tuple.",
            "admin.E018",
        )