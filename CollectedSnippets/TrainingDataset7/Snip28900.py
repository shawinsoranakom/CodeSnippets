def test_non_iterable_item(self):
        class TestModelAdmin(ModelAdmin):
            fieldsets = ({},)

        self.assertIsInvalid(
            TestModelAdmin,
            ValidationTestModel,
            "The value of 'fieldsets[0]' must be a list or tuple.",
            "admin.E008",
        )